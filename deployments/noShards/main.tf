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

# Config Server for the MongoDB
resource "google_compute_instance" "mongos" {
  name = "mongos"
  machine_type = "e2-standard-2"
  allow_stopping_for_update = true
  # Specify the OS image
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
    ssh-keys = "ubuntu:${file("./mongokey.pub")}"
  }
  # Start the script for 
  provisioner "remote-exec" {
    script = "scripts/mongosh.sh"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./mongokey")
    } 
  }
}