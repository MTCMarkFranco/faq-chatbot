# Getting Started 

## To set up the env
Initiate the env for the first time:
```shell
# for linux
python3 -m venv env

# for windows
python -m venv env
```

Activate the env:
```shell
# for linux
source env/bin/activate

# for windows 
.\env\Scripts\activate
```

Install the requirements:
```shell
pip install -r requirements.txt
```

To deactivate the env, enter `deactivate` into the terminal and press `enter`.


## To run the flask app:
```
flask --app app run
```
To run in debug mode (automatically refreshes when changes are made to the files):
```
flask --app app --debug run
```
The app will run on `http://localhost:5000`
