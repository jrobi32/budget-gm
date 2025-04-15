# NBA Team Builder

A web application that allows users to build NBA teams with a $10 budget and simulate their performance.

## Features

- Build a team of 5 players with a $10 budget
- Choose from players in different cost categories ($3, $2, $1, $0)
- Simulate team performance and get projected record
- View player stats after submission

## Deployment Instructions

### Deploying to Python Anywhere

1. Create an account on [Python Anywhere](https://www.pythonanywhere.com/)
2. Upload your project files to Python Anywhere
3. Create a new web app using the Flask framework
4. Set the source code directory to your project directory
5. Set the WSGI configuration file to `wsgi.py`
6. Install the required packages using pip:
   ```
   pip install -r requirements.txt
   ```
7. Reload your web app

### Local Development

1. Clone the repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python app.py
   ```
4. Open your browser and navigate to `http://127.0.0.1:5000`

## Project Structure

- `app.py` - Main Flask application
- `team_builder.py` - Team building logic
- `team_simulator.py` - Team simulation logic
- `models.py` - Data models
- `player_pool.json` - Player data
- `static/` - Static files (CSS, JavaScript)
- `templates/` - HTML templates

## License

This project is licensed under the MIT License - see the LICENSE file for details. 