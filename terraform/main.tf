# ------------------------------------------------------------------------------
# 1. INSTANCE EC2
# ------------------------------------------------------------------------------
/* 
#resource "aws_instance" "cv_analyzer" {
#  ami                    = "ami-0e1c4170d9c01184b"
#  instance_type          = "t3.small"
# availability_zone      = "eu-west-3c"
#  key_name               = "cv-analyzer-key"
 # vpc_security_group_ids = [
#  aws_security_group.launch_wizard_1.id,
 # aws_security_group.allow_k3s_cluster.id]
 # subnet_id              = "subnet-0fbcf3069fea87e20"

  #tags = {
   # Name = "cv-analyzer-test"
  #}
#}

# ------------------------------------------------------------------------------
# 2. DÉFINITION DU SECURITY GROUP
# ------------------------------------------------------------------------------
resource "aws_security_group" "launch_wizard_1" {
  name        = "launch-wizard-1"
  description = "launch-wizard-1 created 2026-07-28T11:54:32.557Z"
  vpc_id      = var.vpc_id


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
*/
# ------------------------------------------------------------------------------
# 5. SECURITY GROUP DÉDIÉ AU CLUSTER K3S (trafic interne uniquement)
# ------------------------------------------------------------------------------

resource "aws_security_group" "allow_k3s_cluster" {
  name        = "k3s-cluster-internal"                  # <- choisis un nom clair, ex: "k3s-cluster-internal"
  description = "k3s-for-orchestration"                  # <- décris son rôle en une phrase
  vpc_id      = var.vpc_id                    # <- ta variable VPC ici
}

# Port API Kubernetes (server <-> agent, et toi via kubectl)
resource "aws_vpc_security_group_ingress_rule" "allow_k3s_api" {
  security_group_id             = aws_security_group.allow_k3s_cluster.id
  referenced_security_group_id = aws_security_group.allow_k3s_cluster.id  # <- lequel ? (relis mon message précédent)
  from_port                     = 6443
  to_port                       = 6443
  ip_protocol                   = "tcp"
}

# Réseau des pods entre nœuds (Flannel VXLAN)
resource "aws_vpc_security_group_ingress_rule" "allow_k3s_vxlan" {
  security_group_id             = aws_security_group.allow_k3s_cluster.id
  referenced_security_group_id = aws_security_group.allow_k3s_cluster.id
  from_port                     = 8472
  to_port                       = 8472
  ip_protocol                   = "udp"  # <- pas tcp cette fois, relis la doc plus haut
}

# Kubelet metrics (server interroge l'agent)
resource "aws_vpc_security_group_ingress_rule" "allow_k3s_kubelet" {
  security_group_id             = aws_security_group.allow_k3s_cluster.id
  referenced_security_group_id = aws_security_group.allow_k3s_cluster.id
  from_port                     = 10250
  to_port                       = 10250
  ip_protocol                   = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "allow_k3s_egress" {
  security_group_id             = aws_security_group.allow_k3s_cluster.id
  referenced_security_group_id = aws_security_group.allow_k3s_cluster.id
  ip_protocol                   = "-1"
}
# ------------------------------------------------------------------------------
# 6. NŒUD MASTER K3S (CONTROL-PLANE)
# ------------------------------------------------------------------------------
resource "aws_instance" "k3s_master" {
  ami                    = "ami-0e1c4170d9c01184b"
  instance_type          = "t3.small"
  availability_zone      = "eu-west-3c"
  key_name               = "cv-analyzer-key"

  vpc_security_group_ids = [
  aws_security_group.k3s_master.id,
  aws_security_group.allow_k3s_cluster.id]

  subnet_id              = "subnet-0fbcf3069fea87e20"

  tags = {
    Name = "k3s-master"
  }
}
# ------------------------------------------------------------------------------
# 7. SECURITY GROUP SSH ADMIN — pour le nœud SERVER (k3s control-plane)
# ------------------------------------------------------------------------------

resource "aws_security_group" "k3s_master" {
  name        = "k3s_master"
  description = "k3s_master pour le noeud k3s_master"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "allow_my_ssh_e2ic" {
  security_group_id = aws_security_group.k3s_master.id
  description        = "EC2 Instance Connect - Paris"
  cidr_ipv4          = "35.180.112.80/29"   # même plage que pour cv_analyzer
  from_port          = 22
  to_port            = 22
  ip_protocol        = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh_my_ip_master" {
  security_group_id = aws_security_group.k3s_master.id
  cidr_ipv4          = var.home_ip_address   # ta variable existante, réutilisée
  from_port          = 22
  to_port            = 22
  ip_protocol        = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "allow_k3s_all_outbound" {
  security_group_id = aws_security_group.k3s_master.id
  cidr_ipv4          = "0.0.0.0/0"
  ip_protocol        = "-1"
}

# ------------------------------------------------------------------------------
# 8. SECURITY GROUP DÉDIÉ — NŒUD AGENT K3S (futur hébergeur de l'appli)
# ------------------------------------------------------------------------------

resource "aws_security_group" "k3s_agent" {
  name        = "k3s_agent"
  description = "Security group pour le noeud agent k3s, accueillera l application via Traefik"
  vpc_id      = var.vpc_id
}

# SSH via EC2 Instance Connect (même plage que les autres instances)
resource "aws_vpc_security_group_ingress_rule" "allow_ssh_e2ic_agent" {
  security_group_id = aws_security_group.k3s_agent.id
  description        = "EC2 Instance Connect - Paris"
  cidr_ipv4          = "35.180.112.80/29"
  from_port          = 22
  to_port            = 22
  ip_protocol        = "tcp"
}

# SSH depuis ton IP perso
resource "aws_vpc_security_group_ingress_rule" "allow_ssh_my_ip_agent" {
  security_group_id = aws_security_group.k3s_agent.id
  cidr_ipv4          = var.home_ip_address
  from_port          = 22
  to_port            = 22
  ip_protocol        = "tcp"
}

# Egress : tout autorisé (pour télécharger k3s, images Docker, etc.)
resource "aws_vpc_security_group_egress_rule" "allow_all_outbound_agent" {
  security_group_id = aws_security_group.k3s_agent.id
  cidr_ipv4          = "0.0.0.0/0"
  ip_protocol        = "-1"
}
resource "aws_vpc_security_group_ingress_rule" "allow_http_agent" {
  security_group_id = aws_security_group.k3s_agent.id
  cidr_ipv4          = "0.0.0.0/0"
  from_port          = 80
  to_port            = 80
  ip_protocol        = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "allow_https_agent" {
  security_group_id = aws_security_group.k3s_agent.id
  cidr_ipv4          = "0.0.0.0/0"
  from_port          = 443
  to_port            = 443
  ip_protocol        = "tcp"
}

# ------------------------------------------------------------------------------
# 9. NŒUD AGENT K3S (exécutera l'appli, dans le cluster)
# ------------------------------------------------------------------------------

resource "aws_instance" "k3s_agent" {
  ami                    = "ami-0e1c4170d9c01184b"
  instance_type          = "t3.small"
  availability_zone      = "eu-west-3c"
  key_name               = "cv-analyzer-key"

  vpc_security_group_ids = [
    aws_security_group.k3s_agent.id,
    aws_security_group.allow_k3s_cluster.id
  ]

  subnet_id = "subnet-0fbcf3069fea87e20"

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name = "k3s-agent"
  }
}

# ------------------------------------------------------------------------------
# 10. PROVISIONING RDS POSTGRESQL
# Créé le 2026-09-03 — Free Tier RDS (750h/mois db.t3.micro + 20 Go gp2)
# RAPPEL EXPIRATION FREE TIER : ~2027-09-03
# ------------------------------------------------------------------------------

# Subnet Group pour RDS (exige au moins 2 sous-réseaux dans des AZ différentes)
resource "aws_db_subnet_group" "rds" {
  name       = "cv-analyzer-rds-subnet-group"
  subnet_ids = [
    "subnet-0fbcf3069fea87e20", # Ton subnet principal (eu-west-3c)
    var.secondary_subnet_id     # Renseigne l'ID d'un 2e subnet dans une autre AZ
  ]

  tags = {
    Name = "cv-analyzer-rds-subnet-group"
  }
}

# Security Group dédié à RDS PostgreSQL
resource "aws_security_group" "rds" {
  name        = "rds-postgres-sg"
  description = "Security group pour la base de donnees RDS PostgreSQL"
  vpc_id      = var.vpc_id

  tags = {
    Name = "rds-postgres-sg"
  }
}

# Ingress 5432 : autorisé uniquement depuis le Security Group du nœud Agent K3s
resource "aws_vpc_security_group_ingress_rule" "allow_postgres_from_agent" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.k3s_agent.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}


# Instance RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier        = "cv-analyzer-db"
  allocated_storage = 20
  storage_type      = "gp2" # Corrected: gp2 est explicitement couvert par le Free Tier
  engine            = "postgres"
  engine_version    = "15" # Si le provider râle au plan, passe à une version mineure fixe (ex: "15.7")
  instance_class    = "db.t3.micro"

  db_name  = "cvanalyzer"
  username = "postgres"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  skip_final_snapshot = true
  publicly_accessible = false

  tags = {
    Name = "cv-analyzer-rds"
  }
}