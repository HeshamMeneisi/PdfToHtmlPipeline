if hash docker 2>/dev/null; then
    echo "Found: docker"
else
    echo "Installing docker ..."
    # Docker
    sudo apt-get install docker -y
    # Use docker without sudo
    sudo service docker start
    sudo usermod -a -G docker ec2-user
    # Auto-start docker
    sudo chkconfig docker on
fi

if hash curl 2>/dev/null; then
  echo "Found: curl"
else
  echo "Installing curl ..."
  sudo apt-get install curl -y
fi

if hash docker-compose 2>/dev/null; then
    echo "Found: docker-compose"
else
    echo "Installing docker-compose ..."
    # Get docker-compose
    sudo curl -L https://github.com/docker/compose/releases/download/1.25.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    docker-compose version
fi

echo "It's recommended to reboot and run this file again"
