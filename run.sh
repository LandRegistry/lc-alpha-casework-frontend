

function finish {
  echo Restarting front-end
  sudo supervisorctl start casework-frontend:casework-frontend-web
}
trap finish EXIT


export LDAP_HOST="10.72.8.22"
export LDAP_PORT="389"
export LDAP_DOMAIN="@diti.lr.net"
export LDAP_SEARCH_DN="OU=CS,OU=Production,DC=diti,DC=lr,DC=net"
export CASEWORKER_GROUP="P334 Land Charges Team"
export ADMIN_GROUP="BlahGroup"
export REPRINT_GROUP="BlahGroup2"
stop casework-frontend
python3 /vagrant/apps/casework-frontend/run.py