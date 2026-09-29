.PHONY: install run test lint evaluate-demo evaluate-dense-dev evaluate-hybrid-dev compare-dev evaluate-dense-holdout evaluate-hybrid-holdout compare-holdout

install:
	python -m pip install -r requirements-dev.txt

run:
	python -m streamlit run app.py

test:
	python -m unittest discover -s tests -v

lint:
	ruff check .

evaluate-demo:
	python scripts/evaluate.py --cases evaluation/questions.json --top-k 5 --output evaluation/results.csv

evaluate-dense-dev:
	python scripts/evaluate_dense.py --cases evaluation/real_questions.json --top-k 5 --output evaluation/real_results_dense_adjudicated.csv

evaluate-hybrid-dev:
	python scripts/evaluate.py --cases evaluation/real_questions.json --top-k 5 --output evaluation/real_results_hybrid_adjudicated.csv

compare-dev:
	python scripts/compare_evaluations.py evaluation/real_results_dense_adjudicated.csv evaluation/real_results_hybrid_adjudicated.csv

evaluate-dense-holdout:
	python scripts/evaluate_dense.py --cases evaluation/holdout_questions.json --top-k 5 --output evaluation/holdout_results_dense.csv

evaluate-hybrid-holdout:
	python scripts/evaluate.py --cases evaluation/holdout_questions.json --top-k 5 --output evaluation/holdout_results_hybrid.csv

compare-holdout:
	python scripts/compare_evaluations.py evaluation/holdout_results_dense.csv evaluation/holdout_results_hybrid.csv
