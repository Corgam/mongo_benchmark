.PHONY: setup mongo benchmark clean

setup:
	ssh-keygen -f deployments/benchmarking_client/clientkey -P "" -q
	ssh-keygen -f deployments/1Shards/clientkey -P "" -q
	ssh-keygen -f deployments/2Shards/clientkey -P "" -q
	ssh-keygen -f deployments/3Shards/clientkey -P "" -q

mongo:
	cd deployments/${n}Shards && terraform init
	cd deployments/${n}Shards && terraform apply -auto-approve

benchmark:
	cd deployments/benchmarking_client && terraform init
	cd deployments/benchmarking_client && terraform apply -auto-approve
	python3 collect_results.py

clean:
	cd deployments/benchmarking_client && terraform destroy -auto-approve
	cd deployments/1Shards && terraform destroy -auto-approve
	cd deployments/2Shards && terraform destroy -auto-approve
	cd deployments/3Shards && terraform destroy -auto-approve
