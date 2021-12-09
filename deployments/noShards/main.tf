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
  name = "imongo"
  machine_type = "f1-micro"
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-93-16623-39-21"
    }
   }
  
  network_interface {
    network = "default"

    access_config {}
  }

  metadata_startup_script = "docker run --name mongodb -p 27017:27017 -d mongo:5.0.4"
}