provider "aws" {
    region = "us-east-1"
}
data "aws_ami" "ubuntu" {
    most_recent = true
  owners      = ["099720109477"]
  filter {
    name ="name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_key_pair" "deployer" {
    key_name = "casino-ssh-key"
    public_key = file("casino_key.pub")
}

resource "aws_security_group" "casino_sg" {
    name = "casion_web_sg"
    description = "Allow HTTP,HTTPS abd SSH inbound trafic"
    ingress {
        description = "HTTP from anywhere"
        from_port  = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}
resource "aws_instance" "casino_server" {
    ami    = data.aws_ami.ubuntu.id 
    instance_type = "t3.micro"
    key_name   = aws_key_pair.deployer.key_name
    vpc_security_group_ids = [aws_security_group.casino_sg.id]
    user_data = <<-EOF
                 #!/bin/bash
                 fallocate -l 2G /swapfile
                 chmod 600 /swapfile
                 mkswap /swapfile
                 swapom /swapfile
                 echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
                 apt-get update
                 apt-get install -y ca-certificates curl gnupg git
                 install -m 0775 -d /etc/apt/keyrings
                 curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                 chmod a+r /etc/apt/keyrings/docker.gpg
                 echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
                 apt-get update
                 apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                 git clone https://github.com/24024102/casino.git /app
                 cd /app
                 docker compose up -d --build
                 EOF

tags = {
    Name = "DevOps-Casino-Production"
  }
}



output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.casino_server.public_ip
}