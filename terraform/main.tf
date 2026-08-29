# ------------------------------------------------------------------------------
# 1. INSTANCE EC2
# ------------------------------------------------------------------------------
resource "aws_instance" "cv_analyzer" {
  ami                    = "ami-0e1c4170d9c01184b"
  instance_type          = "t3.small"
  availability_zone      = "eu-west-3c"
  key_name               = "cv-analyzer-key"
  vpc_security_group_ids = [aws_security_group.launch_wizard_1.id]
  subnet_id              = "subnet-0fbcf3069fea87e20"

  tags = {
    Name = "cv-analyzer-test"
  }
}

# ------------------------------------------------------------------------------
# 2. DÉFINITION DU SECURITY GROUP
# ------------------------------------------------------------------------------
resource "aws_security_group" "launch_wizard_1" {
  name        = "launch-wizard-1"
  description = "launch-wizard-1 created 2026-07-28T11:54:32.557Z"
  vpc_id      = "vpc-0d8d5f86a97f739e3"


}

# ------------------------------------------------------------------------------
# 3. RÈGLES D'ENTRÉE (INGRESS)
# ------------------------------------------------------------------------------

# Trafic Web HTTP classique (Ouvert à tous)
resource "aws_vpc_security_group_ingress_rule" "allow_http" {
  security_group_id = aws_security_group.launch_wizard_1.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

# Port applicatif spécifique 8000 (Ouvert à tous)
resource "aws_vpc_security_group_ingress_rule" "allow_port_8000" {
  security_group_id = aws_security_group.launch_wizard_1.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8000
  to_port           = 8000
  ip_protocol       = "tcp"
}

# Trafic Web sécurisé HTTPS (Ouvert à tous)
resource "aws_vpc_security_group_ingress_rule" "allow_https" {
  security_group_id = aws_security_group.launch_wizard_1.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

# Accès SSH via EC2 Instance Connect (Plage d'IPs AWS /29)
resource "aws_vpc_security_group_ingress_rule" "allow_ssh_e2ic" {
  security_group_id = aws_security_group.launch_wizard_1.id
  description = "EC2 Instance Connect - Paris"
  cidr_ipv4         = "35.180.112.80/29"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

# Accès SSH d'administration (Restreint à ton IP /32)
resource "aws_vpc_security_group_ingress_rule" "allow_ssh_my_ip" {
  security_group_id = aws_security_group.launch_wizard_1.id
  cidr_ipv4         = var.home_ip_address
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

# ------------------------------------------------------------------------------
# 4. RÈGLE DE SORTIE (EGRESS)
# ------------------------------------------------------------------------------

# Autorise tout le trafic sortant vers n'importe quelle destination
resource "aws_vpc_security_group_egress_rule" "allow_all_outbound" {
  security_group_id = aws_security_group.launch_wizard_1.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}