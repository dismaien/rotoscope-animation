# Cloud Strategy

## Working Assumption

Use the Mac for:

- frame extraction
- curation
- contact sheets
- propagation tests
- light scripting

Use cloud GPUs for:

- `FLUX.2 klein` training
- heavier inference benchmarks if needed

## Trial Credit Caution

Google Cloud trial behavior is easy to misunderstand.

- free-trial accounts cannot attach GPUs to VM instances
- Gemini Developer API or AI Studio usage is not the same as normal Google Cloud GPU billing
- after upgrading the account, remaining trial credits may still apply to eligible services, but this should be verified with a tiny dry run before a larger job

## Safe Billing Check

Before the first real training run:

1. launch the smallest practical eligible GPU instance
2. run a `10-minute` smoke test
3. confirm in Billing that the charge was offset by trial credit
4. only then scale to a longer run

## Practical Recommendation

Start with a single A100-class instance for the first paired LoRA run. Do not jump
to a more expensive tier until:

- the trainer stack is working
- the data manifest is reviewed
- the first smoke test confirms billing behavior
