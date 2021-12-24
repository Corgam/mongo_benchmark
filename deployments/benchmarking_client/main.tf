terraform {
  required_providers {
      google = {
          source = "hashicorp/google"
          version = "3.5.0"
      }
  }
}

provider "google" {
  project = "351640241283"
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
  # Upload the config file
  provisioner "file" {
    source = "../../config.toml"
    destination = "/tmp/config.toml"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
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
}