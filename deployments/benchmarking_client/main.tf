terraform {
  required_providers {
      google = {
          source = "hashicorp/google"
          version = "3.5.0"
      }
  }
}

provider "google" {
  credentials = file("./../../credentials.json")
  project = "mongodb-benchmark"
  region = "europe-west1"
  zone = "europe-west1-b"
}

resource "google_compute_instance" "benchmarking_client" {
  name = "client"
  machine_type = "e2-standard-2"
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-minimal-2004-focal-v20211209"
    }
   }
  
  network_interface {
    network = "default"
    access_config {}
  }
  # Upload the ssh public key
  metadata = {
    ssh-keys = "ubuntu:${file("./clientkey.pub")}"
  }
  # Upload the requirements file
  provisioner "file" {
    source = "requirements.txt"
    destination = "/tmp/requirements.txt"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Upload the workload file
  provisioner "file" {
    source = "../../workload_generation/workload.json.gz"
    destination = "/tmp/workload.json.gz"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Upload the python file
  provisioner "file" {
    source = "src/client.py"
    destination = "/tmp/client.py"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Start the python script
  provisioner "remote-exec" {
    script = "scripts/client.sh"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
}

resource "local_file" "clientIP" {
    depends_on = [google_compute_instance.benchmarking_client]
    content = "${google_compute_instance.benchmarking_client.network_interface.0.access_config.0.nat_ip}"
    filename = "clientIP.txt"
}