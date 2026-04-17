#!/usr/bin/env python3
"""unsloth + QLoRA 파인튜닝 스크립트.

AI Safety/Security 실습용 취약 모델을 QLoRA 방식으로 파인튜닝한다.
기반 모델의 가중치를 직접 수정하여 시스템 프롬프트 의존 없이 원하는 동작을 학습시킨다.

Usage:
  source ~/finetune-env/bin/activate
  python3 qlora_finetune.py --model gemma-3-4b-it --epochs 3 --output ccc-safety-4b
  python3 qlora_finetune.py --model Llama-3.2-3B-Instruct --epochs 3 --output ccc-safety-3b

Requirements: unsloth, torch (CUDA), datasets, trl, peft, bitsandbytes
"""
import argparse
import json
import os

def main():
    # Disable torch.compile/Triton issues on DGX Spark
    os.environ["TORCHDYNAMO_DISABLE"] = "1"
    os.environ["UNSLOTH_COMPILE_DISABLE"] = "1"

    parser = argparse.ArgumentParser(description="QLoRA fine-tuning for AI Safety labs")
    parser.add_argument("--model", default="unsloth/gemma-3-4b-it",
                        help="Base model (HuggingFace ID or local path)")
    parser.add_argument("--dataset", default="dataset/comprehensive_safety.jsonl",
                        help="Training data (JSONL with messages field)")
    parser.add_argument("--output", default="ccc-safety-qlora",
                        help="Output model name")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-seq-len", type=int, default=2048)
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=16, help="LoRA alpha")
    parser.add_argument("--gguf", action="store_true", help="Export to GGUF after training")
    parser.add_argument("--quant", default="q4_k_m", help="GGUF quantization method")
    args = parser.parse_args()

    print(f"=== QLoRA Fine-tuning ===")
    print(f"Model: {args.model}")
    print(f"Dataset: {args.dataset}")
    print(f"Output: {args.output}")
    print(f"Epochs: {args.epochs}, LR: {args.lr}, Batch: {args.batch_size}")
    print(f"LoRA: r={args.lora_r}, alpha={args.lora_alpha}")
    print()

    # ── 1. Load model with QLoRA ──
    from unsloth import FastLanguageModel
    import torch

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_seq_len,
        load_in_4bit=True,  # QLoRA: 4-bit quantization
        dtype=None,  # Auto-detect
    )
    print(f"Model loaded: {args.model} (4-bit quantized)")

    # ── 2. Apply LoRA adapters ──
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                         "gate_proj", "up_proj", "down_proj"],
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )
    print(f"LoRA adapters applied: r={args.lora_r}, alpha={args.lora_alpha}")
    model.print_trainable_parameters()

    # ── 3. Load & format dataset ──
    data_path = os.path.join(os.path.dirname(__file__), "..", args.dataset)
    raw_data = []
    with open(data_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if "messages" in item:
                raw_data.append(item)
            elif "prompt" in item and "response" in item:
                raw_data.append({
                    "messages": [
                        {"role": "user", "content": item["prompt"]},
                        {"role": "assistant", "content": item["response"]},
                    ]
                })

    print(f"Dataset: {len(raw_data)} samples loaded")

    # Format into chat template
    from unsloth.chat_templates import get_chat_template
    tokenizer = get_chat_template(tokenizer, chat_template="gemma-3")

    def format_sample(sample):
        text = tokenizer.apply_chat_template(
            sample["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    from datasets import Dataset
    dataset = Dataset.from_list(raw_data)
    dataset = dataset.map(format_sample)
    print(f"Dataset formatted: {len(dataset)} samples")
    print(f"Sample: {dataset[0]['text'][:200]}...")

    # ── 4. Training ──
    from trl import SFTTrainer
    from transformers import TrainingArguments

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output", args.output)
    os.makedirs(output_dir, exist_ok=True)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=TrainingArguments(
            output_dir=output_dir,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            num_train_epochs=args.epochs,
            learning_rate=args.lr,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=42,
            report_to="none",
            save_strategy="epoch",
        ),
        data_collator=None,
    )

    print(f"\n=== Training started ({args.epochs} epochs) ===")
    stats = trainer.train()
    print(f"\n=== Training complete ===")
    print(f"  Loss: {stats.training_loss:.4f}")
    print(f"  Runtime: {stats.metrics['train_runtime']:.1f}s")

    # ── 5. Save model ──
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to: {output_dir}")

    # ── 6. Export to GGUF (optional) ──
    if args.gguf:
        gguf_dir = os.path.join(output_dir, "gguf")
        os.makedirs(gguf_dir, exist_ok=True)
        print(f"\n=== Exporting to GGUF ({args.quant}) ===")
        model.save_pretrained_gguf(
            gguf_dir,
            tokenizer,
            quantization_method=args.quant,
        )
        print(f"GGUF saved to: {gguf_dir}")

        # Create Ollama Modelfile
        gguf_files = [f for f in os.listdir(gguf_dir) if f.endswith(".gguf")]
        if gguf_files:
            modelfile_path = os.path.join(gguf_dir, "Modelfile")
            with open(modelfile_path, "w") as mf:
                mf.write(f"FROM ./{gguf_files[0]}\n\n")
                mf.write('SYSTEM """You are a cybersecurity training AI.\n')
                mf.write("Safety labels: REFUSED, COMPLIED, BLOCKED, FILTERED\n")
                mf.write("Content labels: SAFE, HARMFUL, SUSPICIOUS, BENIGN\n")
                mf.write("Guardrail labels: ALLOW, DENY, TRUNCATED, VALID, BUDGET_EXCEEDED\n")
                mf.write('Always respond in the same language as the user."""\n\n')
                mf.write("PARAMETER temperature 0.7\n")
                mf.write("PARAMETER num_predict 512\n")
            print(f"Modelfile created: {modelfile_path}")
            print(f"\nTo register with Ollama:")
            print(f"  cd {gguf_dir}")
            print(f"  ollama create {args.output} -f Modelfile")

    # ── 7. Save training report ──
    report = {
        "model": args.model,
        "output": args.output,
        "dataset_size": len(raw_data),
        "epochs": args.epochs,
        "lr": args.lr,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "final_loss": stats.training_loss,
        "runtime_seconds": stats.metrics["train_runtime"],
        "gguf_exported": args.gguf,
    }
    report_path = os.path.join(output_dir, "training_report.json")
    json.dump(report, open(report_path, "w"), indent=2, ensure_ascii=False)
    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    main()
