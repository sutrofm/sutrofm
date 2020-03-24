# -*- mode: ruby -*-
# vi: set ft=ruby :

unless Vagrant.has_plugin?("vagrant-hostmanager")
  STDERR.puts <<-EOF
Please install the vagrant-hostmanager plugin:
  $ vagrant plugin install vagrant-hostmanager
  EOF

  exit
end

Vagrant.configure("2") do |config|
  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.ignore_private_ip = false
  config.hostmanager.include_offline = true

  config.vm.box = "bento/ubuntu-14.04"
  config.vm.hostname = "sutrofm.dev"
  config.vm.provision "shell", path: "scripts/sutrofm_deps.sh"
  config.vm.network "private_network", ip: "192.168.11.22"
end
