#!/bin/bash -e

# clones specified branch of specified repo
# builds guides, captures output
# installs httpd, spits out URLs
# yes, this would be simpler in a Dockerfile
# but Docker isn't available on the web by default

# repo and branch defaults
REPO_URL_DEFAULT="https://github.com/IQSS/dataverse.git"
BRANCH_DEFAULT="develop"
PEM_DEFAULT=${HOME}

# centos image list at https://wiki.centos.org/Cloud/AWS
# centos 8.2, us-east-1
AWS_AMI_DEFAULT='ami-01ca03df4a6012157'

usage() {
  echo "Usage: $0 -b <branch> -r <repo> -p <pem_dir> -i aws_image -s aws_size -t aws_tag -d" 1>&2
  echo "default branch is develop"
  echo "default repo is https://github.com/IQSS/dataverse"
  echo "default .pem location is ${HOME}"
  echo "default AWS AMI ID is $AWS_AMI_DEFAULT"
  echo "default AWS size is t2.micro for free tier"
  echo "-d will destroy ("terminate") the AWS instance once build completes"
  exit 1
}

while getopts ":r:b:p:i:s:t:d" o; do
  case "${o}" in
  r)
    REPO_URL=${OPTARG}
    ;;
  b)
    BRANCH=${OPTARG}
    ;;
  p)
    PEM_DIR=${OPTARG}
    ;;
  i)
    AWS_IMAGE=${OPTARG}
    ;;
  s)
    AWS_SIZE=${OPTARG}
    ;;
  t)
    TAG=${OPTARG}
    ;;
  l)
    LOCAL_LOG_PATH=${OPTARG}
    ;;
  d)
    DESTROY=true
    ;;
  *)
    usage
    ;;
  esac
done

# test for CLI args
if [ -z "$REPO_URL" ]; then
   REPO_URL="$REPO_URL_DEFAULT"
   echo "using repo $REPO_URL"
fi

if [ -z "$BRANCH" ]; then
   BRANCH="$BRANCH_DEFAULT"
   echo "building branch $BRANCH"
fi

if [ ! -z "$AWS_IMAGE" ]; then
   AMI_ID=$AWS_IMAGE
else
   AMI_ID="$AWS_AMI_DEFAULT"
fi 
echo "using $AMI_ID"

if [ ! -z "$AWS_SIZE" ]; then
   SIZE=$AWS_SIZE
else
   SIZE="t2.micro"
fi
echo "using $SIZE"

if [ ! -z "$TAG" ]; then
   TAGARG="--tag-specifications ResourceType=instance,Tags=[{Key=name,Value=$TAG}]"
   echo "using tag $TAG"
fi

if [ -z "$PEM_DIR" ]; then
   PEM_DIR="$PEM_DEFAULT"
fi

AWS_CLI_VERSION=$(aws --version)
if [[ "$?" -ne 0 ]]; then
  echo 'The "aws" program could not be executed. Is it in your $PATH?'
  exit 1
fi

if [[ $(git ls-remote --heads $REPO_URL $BRANCH | wc -l) -eq 0 ]]; then
  echo "Branch \"$BRANCH\" does not exist at $REPO_URL"
  usage
  exit 1
fi

# dataverse-sg is fine, just need http open
SECURITY_GROUP='dataverse-sg'
GROUP_CHECK=$(aws ec2 describe-security-groups --group-name $SECURITY_GROUP)
if [[ "$?" -ne 0 ]]; then
  echo "Creating security group \"$SECURITY_GROUP\"."
  aws ec2 create-security-group --group-name $SECURITY_GROUP --description "security group for Dataverse"
  aws ec2 authorize-security-group-ingress --group-name $SECURITY_GROUP --protocol tcp --port 22 --cidr 0.0.0.0/0
  aws ec2 authorize-security-group-ingress --group-name $SECURITY_GROUP --protocol tcp --port 80 --cidr 0.0.0.0/0
fi

RANDOM_STRING="$(uuidgen | cut -c-8)"
KEY_NAME="key-$USER-$RANDOM_STRING"

PRIVATE_KEY=$(aws ec2 create-key-pair --key-name $PEM_DIR/$KEY_NAME --query 'KeyMaterial' --output text)
if [[ $PRIVATE_KEY == '-----BEGIN RSA PRIVATE KEY-----'* ]]; then
  PEM_FILE="$PEM_DIR/$KEY_NAME.pem"
  printf -- "$PRIVATE_KEY" >$PEM_FILE
  chmod 400 $PEM_FILE
  echo "Your newly created private key file is \"$PEM_FILE\". Keep it secret. Keep it safe."
else
  echo "Could not create key pair. Exiting."
  exit 1
fi

echo "Creating EC2 instance"
# TODO: Add some error checking for "ec2 run-instances".
INSTANCE_ID=$(aws ec2 run-instances --image-id $AMI_ID --security-groups $SECURITY_GROUP $TAGARG --count 1 --instance-type $SIZE --key-name $PEM_DIR/$KEY_NAME --query 'Instances[0].InstanceId' --block-device-mappings '[ { "DeviceName": "/dev/sda1", "Ebs": { "DeleteOnTermination": true } } ]' | tr -d \")
echo "Instance ID: "$INSTANCE_ID

DESTROY_CMD="aws ec2 terminate-instances --instance-ids $INSTANCE_ID"
echo "When you are done, please terminate your instance with:"
echo "$DESTROY_CMD"
echo "giving instance 120 seconds to wake up..."
echo "t2.micro is free-tier but sloooow to boot up"

sleep 120
echo "End creating EC2 instance"

PUBLIC_DNS=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[*].Instances[*].[PublicDnsName]" --output text)
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[*].Instances[*].[PublicIpAddress]" --output text)

USER_AT_HOST="centos@${PUBLIC_DNS}"
echo "New instance created with ID \"$INSTANCE_ID\". To ssh into it:"
echo "ssh -i $PEM_FILE $USER_AT_HOST"

echo "Please wait at least 15 minutes while the branch \"$BRANCH\" from $REPO_URL is being deployed."

if [ ! -z "$GRPVRS" ]; then
   scp -i $PEM_FILE -o 'StrictHostKeyChecking no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=300' $GRPVRS $USER_AT_HOST:$GVFILE
fi

# epel-release is installed first to ensure the latest ansible is installed after
# TODO: Add some error checking for this ssh command.
ssh -T -i $PEM_FILE -o 'StrictHostKeyChecking no' -o 'UserKnownHostsFile=/dev/null' -o 'ConnectTimeout=300' $USER_AT_HOST <<EOF
sudo yum -y install epel-release
sudo dnf config-manager --enable PowerTools
sudo yum -y install git make graphviz httpd python3-sphinx
git clone -b $BRANCH $REPO_URL dataverse
cd ~/dataverse/doc/sphinx-guides
make clean
mkdir -p ~/dataverse/doc/sphinx-guides/build/html
make html > build/html/build.out 2>&1
make epub >> build/html/build.out 2>&1 
cp build/epub/Dataverse.epub build/html
sudo mkdir -p "/var/www/html/$BRANCH"
sudo rsync -av ~/dataverse/doc/sphinx-guides/build/html/ /var/www/html/$BRANCH/
sudo rm /etc/httpd/conf.d/welcome.conf
sudo systemctl start httpd
EOF

if [ ! -z "$LOCAL_LOG_PATH" ]; then
   echo "copying logs to $LOCAL_LOG_PATH."
   # 1 accept SSH keys
   ssh-keyscan ${PUBLIC_DNS} >> ~/.ssh/known_hosts
   # 2 logdir should exist
   mkdir -p $LOCAL_LOG_PATH
   # 3 grab build output 
   rsync -av -e "ssh -i $PEM_FILE" --ignore-missing-args centos@$PUBLIC_DNS:dataverse/doc/sphinx-guides/build/html/build.out $LOCAL_LOG_PATH/
fi

CLICKABLE_LINK="http://${PUBLIC_DNS}"
echo "Guides from $BRANCH have been written to $CLICKABLE_LINK"

if [ -z "$DESTROY" ]; then
   echo "To ssh into the new instance:"
   echo "ssh -i $PEM_FILE $USER_AT_HOST"
   echo "When you are done, please terminate your instance with:"
   echo "$DESTROY_CMD"
else
   echo "destroying AWS instance"
   eval $DESTROY_CMD
   echo "removing EC2 PEM"
   rm -f $PEM_FILE
fi
