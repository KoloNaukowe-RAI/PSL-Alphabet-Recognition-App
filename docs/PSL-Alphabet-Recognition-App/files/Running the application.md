### 1. Before the first launch  
  
Make sure you have Python 3.12.0 installed on your computer. If yes, you need to install the required packages. To do this, run the following command in terminal inside the project directory:  
```commandline  
pip install -r requirements.txt  
```  
  
Make the migrations and migrate the database:  
```commandline  
python manage.py makemigrations  
python manage.py migrate  
```  
To create superuser:   
```commandline  
python manage.py createsuperuser  
```  
  
### 2. Launching the application  
  
To run the application run the following command in terminal inside the project directory:  
```commandline  
python manage.py runserver  
```

### Go to:
- [[Index]]
- [[Application description]]
- [[Technologies]]
- [[Authors]]
- [[Summary]]