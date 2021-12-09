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

resource "google_compute_instance" "mongodb" {
  name = "configserver"
  machine_type = "e2-standard-2"
  allow_stopping_for_update = true
  # Specify the image as: container optimized OS
  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-93-16623-39-21"
    }
   }
  
  network_interface {
    network = "default"
    access_config {}
  }
  # Run the mongo container from uploaded image
  metadata_startup_script = "${file("./cos_startup.sh")}"
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
}