# AWS EC2 installation without using Docker

Create the EC2 instance as given [here(aws phase 1)](https://github.com/testpress/open-event-droidgen/blob/development/docs/installation/aws.md#phase-1)

Note: Add custom TCP (inbound)rule to support 8080 port in security group.

### Cloning the Project
```bash
sudo apt-get install git
git clone https://github.com/fossasia/open-event-android.git && cd open-event-android
export PROJECT_DIR=$(pwd)
```

### Installing the requirements

#### Installing dependencies

```bash
sudo dpkg --add-architecture i386
sudo apt-get install -y software-properties-common git wget libc6-i386 lib32stdc++6 lib32gcc1 lib32ncurses5 lib32z1 curl libqt5widgets5
sudo apt-get install -y ca-certificates && update-ca-certificates
```

#### Installing Python 2.7.x

```bash
sudo apt-get install -y --no-install-recommends build-essential python python-dev python-pip libpq-dev libevent-dev libmagic-dev zip unzip expect
```

#### Installing Oracle JDK 8
```bash
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer oracle-java8-set-default
```

#### Installing Android SDK
```bash
sudo cp -r kubernetes/images/generator/tools /opt
sudo bash ./kubernetes/images/generator/android.sh
```

##### Installing Redis
- If you do not have Redis already, you can install by
```bash
# Download source
wget http://download.redis.io/releases/redis-stable.tar.gz
# Unzip source
tar xzf redis-stable.tar.gz
cd redis-stable
# Compile source
make
# Install redis
sudo make install
# Start redis server in the background
redis-server &
```

### Installing the project requirements

Let's go into the app generator's directory
```bash
cd /apk-generator/v2/
```
#### Installing python dependencies
```bash
sudo pip install -U pip
sudo pip install --upgrade setuptools
sudo pip install --upgrade distribute
sudo -H pip install -r requirements.txt
```

Copy following inside ~/.bash_aliases

```bash
export ANDROID_HOME="/opt/android-sdk-linux"

export PATH=${PATH}:${ANDROID_HOME}/tools:${ANDROID_HOME}/platform-tools

export KEY_ALIAS=testpress
export KEYSTORE_PASSWORD=welcome1$
export KEYSTORE_PATH=/home/ubuntu/testpress.jks

export GENERATOR_WORKING_DIR=/home/ubuntu/temp/
```

Copy `testpress.jks` to home folder of ec2

```bash
scp -i path_to_pem_file path_to_testpress_jks path_to_ec2
```

Eg.
```bash
scp -i ~/Documents/apk_generator.pem ~/Documents/documents/testpress.jks ubuntu@ec2-13-232-46-108.ap-south-1.compute.amazonaws.com:~/
```

##### Starting celery worker in the background
```bash
celery worker -A app.celery &
```
##### Note: The '&' in the above command means detaching from the console. To avoid use the following command instead
```bash
celery worker -A app.celery --loglevel=INFO
```
##### Starting the app generator web server
```bash
gunicorn -b 0.0.0.0:8080 app:app --enable-stdio-inheritance --log-level "info"
```

Redirect port 80 to 8080 and make it work on local machine
```
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8080
```
