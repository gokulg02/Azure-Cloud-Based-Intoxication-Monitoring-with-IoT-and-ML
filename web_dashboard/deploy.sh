#Install python, node.js, npm and SQL Server ODBC driver
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nodejs npm nginx git unixodbc unixodbc-dev
nvm install 23.7
nvm use 23.7
nvm alias default 23.7
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.6/install.sh | bash
source ~/.bashrc
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt update
sudo ACCEPT_EULA=Y apt install -y msodbcsql18 mssql-tools18
echo "All dependencies installed"

#Pull files from GitHub repo
git clone https://github.com/gokulg02/Azure-Cloud-Based-Intoxication-Monitoring-with-IoT-and-ML.git
cd ~/Azure-Cloud-Based-Intoxication-Monitoring-with-IoT-and-ML/web_dashboard/

# Set up Python virtual environment for Flask
echo "Setting up Flask"
cd ./services/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn
deactivate
export SQL_CONN_STR="Replace with Azure SQL Database connection string"

# Build frontend
echo "Building frontend"
cd ../app
npm install
npm run build

# Configure Nginx
echo "Configuring Nginx"
NGINX_CONF="/etc/nginx/sites-available/app.conf"

sudo bash -c "cat > $NGINX_CONF" <<EOL
server {
    listen 80;
    server_name _;

    root /home/azureuser/Azure-Cloud-Based-Intoxication-Monitoring-with-IoT-and-ML/web_dashboard/app/build;
    index index.html;

    location / {
        try_files \$uri /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOL

sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo systemctl restart nginx

#Start Flask app
echo "Running Flask app using gunicorn"
SERVICE_FILE="/etc/systemd/system/flask.service"
USERNAME=$(whoami)
WORKDIR="/home/$USERNAME/Azure-Cloud-Based-Intoxication-Monitoring-with-IoT-and-ML/web_dashboard/services"

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Gunicorn instance to serve Flask app
After=network.target

[Service]
User=$USERNAME
Group=www-data
WorkingDirectory=$WORKDIR
Environment=\"PATH=$WORKDIR/venv/bin\"
ExecStart=$WORKDIR/venv/bin/gunicorn -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl start flask
sudo systemctl enable flask

echo "Setup complete"