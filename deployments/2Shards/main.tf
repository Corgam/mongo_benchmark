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
resource "google_compute_instance" "mongodb" {
  name = "configserver"
  machine_type = "e2-standard-2"
  allow_stopping_for_update = true
  # Specify the image as: container optimized OS
  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-minimal-2110-impish-v20211207"
    }
   }
  
  network_interface {
    network = "default"
    access_config {}
  }
  # Run the mongo container from uploaded image
  metadata_startup_script = "sudo docker run --name mongodb -p 27017:27017 -d mongo:5.0.4"
  # Upload the ssh public key
  metadata = {
    ssh-keys = "ubuntu:${file("./mongokey.pub")}"
  }
  # Upload the config file for the configserver mongo
  provisioner "file" {
    source = "configserver.conf"
    destination = "/tmp/configserver.conf"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./mongokey")
    } 
  }
  # Upload the js file for init
  provisioner "file" {
    source = "init.js"
    destination = "/tmp/init.js"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./mongokey")
    } 
  }
  # Upload the script for the init
  # provisioner "file" {
  #   source = "scripts/mongo_startup.sh"
  #   destination = "/tmp/mongo_startup.sh"
  #   connection {
  #     type = "ssh"
  #     user = "ubuntu"
  #     host = self.network_interface[0].access_config[0].nat_ip
  #     private_key = file("./mongokey")
  #   } 
  # }
  # Start the script for 
  provisioner "remote-exec" {
    script = "scripts/config_server_startup.sh"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./mongokey")
    } 
  }
}