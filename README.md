# Telegram Bot Backend

This project is a backend service built using Python and [Poetry](https://python-poetry.org/), designed to configure and manage a Telegram bot. The backend leverages [Supabase](https://supabase.com/) as its database and storage solution, and it serves as the backend for the website [DeFi Sins](https://defi-sins.netlify.app/).

## Features

- **Telegram Bot Integration**: Provides seamless communication with Telegram users via the Telegram Bot API.
- **Supabase Integration**: Uses Supabase for managing data storage, authentication, and real-time capabilities.
- **Scalable Architecture**: Designed with scalability in mind to handle multiple user interactions effectively.
- **API Backend for DeFi Sins**: Serves as the backend for the website [DeFi Sins](https://defi-sins.netlify.app/).

## Prerequisites

- **Python**: Ensure Python 3.8 or higher is installed.
- **Poetry**: Install Poetry for dependency management. [Installation guide](https://python-poetry.org/docs/#installation).
- **Supabase Account**: A Supabase project for database and storage.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo-name.git
   cd your-repo-name
   ```

2. Install dependencies:

   ```bash
   poetry install
   ```

3. Configure environment variables:

   Create a `.env` file in the project root and add your Supabase and Telegram Bot API keys:

   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ```

4. Run database migrations (if applicable):

   ```bash
   poetry run python manage.py migrate
   ```

## Usage

1. Start the bot:

   ```bash
   poetry run python main.py
   ```

2. The backend will automatically connect to the Telegram Bot API and Supabase.

3. Ensure the frontend at [DeFi Sins](https://defi-sins.netlify.app/) is properly configured to interact with this backend.

## Project Structure

```
├── main.py                 # Entry point for the bot backend
├── config/                 # Configuration files (e.g., database, bot settings)
├── utils/                  # Utility functions for various tasks
├── requirements.txt        # Dependencies (generated by Poetry)
├── .env                    # Environment variables
└── README.md               # Project documentation
```

## Deployment

- This backend can be deployed on any cloud platform (AWS, GCP, Heroku, etc.) or containerized using Docker.
- Ensure to provide environment variables in the production environment.

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Commit your changes: `git commit -m 'Add a new feature'`.
4. Push to the branch: `git push origin feature-name`.
5. Submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.