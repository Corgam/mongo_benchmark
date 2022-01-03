.PHONY: setup-mongo benchmark

setup-mongo:
	cd deployments/${N}Shards && terraform apply -auto-approve

benchmark:
	cd deployments/benchmarking_client && terraform apply -auto-approve

clean:
	cd deployments/benchmarking_client && terraform destroy -auto-approve
	cd deployments/1Shards && terraform destroy -auto-approve
	cd deployments/2Shards && terraform destroy -auto-approve
	cd deployments/3Shards && terraform destroy -auto-approve
