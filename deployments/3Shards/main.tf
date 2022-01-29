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

# Config Server for the MongoDB
resource "google_compute_instance" "configserver" {
  name = "configserver"
  machine_type = "e2-standard-4"
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
    ssh-keys = "ubuntu:${file("./clientkey.pub")}"
  }
  # Upload the config file for the configserver mongo
  provisioner "file" {
    source = "mongo_configs/configserver.conf"
    destination = "/tmp/configserver.conf"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Upload the js file for init
  provisioner "file" {
    source = "scripts/initiate.js"
    destination = "/tmp/initiate.js"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Start the script for 
  provisioner "remote-exec" {
    script = "scripts/config_server_startup.sh"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
}

# Shard 1 for the MongoDB
resource "google_compute_instance" "shard1" {
  name = "shard1"
  machine_type = "e2-standard-4"
  allow_stopping_for_update = true
  # Specify the image as: container optimized OS
  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-minimal-2004-focal-v20211209"
    }
   }
  
  network_interface {
    network = "default"
    #network_ip = "10.132.0.51"
    access_config {}
  }
  # Upload the ssh public key
  metadata = {
    ssh-keys = "ubuntu:${file("./clientkey.pub")}"
  }
  # Upload the config file for the configserver mongo
  provisioner "file" {
    source = "mongo_configs/shard1.conf"
    destination = "/tmp/shard1.conf"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Upload the js file for init
  provisioner "file" {
    source = "scripts/initiate.js"
    destination = "/tmp/initiate.js"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Start the script for 
  provisioner "remote-exec" {
    script = "scripts/shard1_startup.sh"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
}

# Shard 2 for the MongoDB
resource "google_compute_instance" "shard2" {
  name = "shard2"
  machine_type = "e2-standard-4"
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
    ssh-keys = "ubuntu:${file("./clientkey.pub")}"
  }
  # Upload the config file for the configserver mongo
  provisioner "file" {
    source = "mongo_configs/shard2.conf"
    destination = "/tmp/shard2.conf"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Upload the js file for init
  provisioner "file" {
    source = "scripts/initiate.js"
    destination = "/tmp/initiate.js"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Start the script for 
  provisioner "remote-exec" {
    script = "scripts/shard2_startup.sh"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
}

# Shard 3 for the MongoDB
resource "google_compute_instance" "shard3" {
  name = "shard3"
  machine_type = "e2-standard-4"
  allow_stopping_for_update = true
  # Specify the image as: container optimized OS
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
  # Upload the config file for the configserver mongo
  provisioner "file" {
    source = "mongo_configs/shard3.conf"
    destination = "/tmp/shard3.conf"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Upload the js file for init
  provisioner "file" {
    source = "scripts/initiate.js"
    destination = "/tmp/initiate.js"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Start the script for 
  provisioner "remote-exec" {
    script = "scripts/shard3_startup.sh"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
}

# Mongos router
resource "google_compute_instance" "mongos" {
  name = "mongos"
  machine_type = "e2-standard-4"
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
    ssh-keys = "ubuntu:${file("./clientkey.pub")}"
  }
  # Upload the config file for the configserver mongo
  provisioner "file" {
    source = "mongo_configs/mongos.conf"
    destination = "/tmp/mongos.conf"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Upload the js file for init
  provisioner "file" {
    source = "scripts/mongos.js"
    destination = "/tmp/mongos.js"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
  # Start the script for 
  provisioner "remote-exec" {
    script = "scripts/mongos.sh"
    connection {
      type = "ssh"
      user = "ubuntu"
      host = self.network_interface[0].access_config[0].nat_ip
      private_key = file("./clientkey")
    } 
  }
}