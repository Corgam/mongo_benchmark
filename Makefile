.PHONY: setup mongo benchmark clean

setup:
	sudo apt-get -y install git

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
