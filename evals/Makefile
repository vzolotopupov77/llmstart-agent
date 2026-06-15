CONFIG  ?= configs/baseline-react-chroma.yaml
DATASET ?= all
RUN     ?=
RUN_A   ?=
RUN_B   ?=

.PHONY: validate sync experiment analyze compare backfill-runs help

help:
	@echo "Eval contour targets (E-2): validate sync experiment analyze compare backfill-runs"

validate:
	uv run pytest tests/ -q
	uv run python -m scripts.sync_datasets --validate-only --dataset $(DATASET)
	uv run python -m scripts.check_langfuse_versions
	uv run python -m scripts.check_langfuse_contracts

sync: validate
	uv run python -m scripts.sync_datasets --dataset $(DATASET)

experiment: sync
	uv run python -m scripts.run_experiment --config $(CONFIG) --dataset $(DATASET)

analyze:
	uv run python -m scripts.analyze_run --run "$(RUN)" --out reports/

compare:
	uv run python -m scripts.compare_runs --a "$(RUN_A)" --b "$(RUN_B)" --out reports/

backfill-runs:
	uv run python -m scripts.backfill_dataset_run_items $(if $(RUN),--run "$(RUN)",)
