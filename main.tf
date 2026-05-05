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
