#!/usr/bin/env python3
"""순수 transformers + PEFT + trl 기반 QLoRA 파인튜닝 (unsloth/Triton 불필요).

DGX Spark (GB10, CUDA 13.0, aarch64) 환경에서 Triton 빌드 오류를 회피.
unsloth의 속도 최적화는 포기하되, 학습 자체는 정상 동작.

Usage:
  source ~/finetune-env/bin/activate
  python3 qlora_vanilla.py --model google/gemma-3-4b-it --output ccc-safety-4b
"""
import argparse, json, os

os.environ["TORCHDYNAMO_DISABLE"] = "1"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="meta-llama/Llama-3.2-3B-Instruct")
    parser.add_argument("--dataset", default="dataset/comprehensive_safety.jsonl")
    parser.add_argument("--output", default="ccc-safety-vanilla")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=16)
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer, SFTConfig
    from datasets import Dataset

    print(f"=== QLoRA (vanilla transformers) ===")
    print(f"Model: {args.model}")
    print(f"torch={torch.__version__} cuda={torch.cuda.is_available()}")

    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    print("Loading model (4-bit)...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        attn_implementation="eager",  # Flash Attention 불필요
    )
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)

    # LoRA config
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                         "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load dataset
    data_path = os.path.join(os.path.dirname(__file__), "..", args.dataset)
    raw = []
    with open(data_path) as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            if "messages" in item:
                raw.append(item)
            elif "prompt" in item:
                raw.append({"messages": [
                    {"role": "user", "content": item["prompt"]},
                    {"role": "assistant", "content": item["response"]},
                ]})
    print(f"Dataset: {len(raw)} samples")

    def format_fn(sample):
        text = tokenizer.apply_chat_template(
            sample["messages"], tokenize=False, add_generation_prompt=False
        )
        return {"text": text}

    dataset = Dataset.from_list(raw).map(format_fn)

    # Training
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", args.output)
    os.makedirs(out_dir, exist_ok=True)

    training_args = SFTConfig(
        output_dir=out_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        bf16=True,
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        report_to="none",
        save_strategy="epoch",
    )
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=training_args,
    )

    print(f"\n=== Training ({args.epochs} epochs) ===")
    stats = trainer.train()
    print(f"\n=== Done ===")
    print(f"  Loss: {stats.training_loss:.4f}")
    print(f"  Time: {stats.metrics['train_runtime']:.1f}s")

    # Save LoRA adapter
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)
    print(f"Saved to: {out_dir}")

    # Save report
    report = {
        "model": args.model, "output": args.output,
        "dataset_size": len(raw), "epochs": args.epochs,
        "lr": args.lr, "lora_r": args.lora_r, "lora_alpha": args.lora_alpha,
        "final_loss": stats.training_loss,
        "runtime_seconds": stats.metrics["train_runtime"],
        "method": "QLoRA (vanilla transformers + PEFT + trl)",
        "quantization": "nf4 (4-bit)",
    }
    json.dump(report, open(os.path.join(out_dir, "training_report.json"), "w"),
              indent=2, ensure_ascii=False)
    print(f"Report: {out_dir}/training_report.json")


if __name__ == "__main__":
    main()
