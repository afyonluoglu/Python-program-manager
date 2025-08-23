# Python Program Manager

A comprehensive desktop application for managing and organizing Python programs, scripts, and projects with an intuitive graphical user interface.

## 🚀 Features

- **Program Organization**: Categorize and manage your Python scripts and projects
- **Quick Launch**: Execute Python programs directly from the interface
- **Project Management**: Create, edit, and organize Python projects
- **User-Friendly GUI**: Built with Tkinter for cross-platform compatibility
- **High DPI Support**: Optimized for modern high-resolution displays
- **Lightweight**: Minimal resource usage with fast startup times

## 📋 Requirements

- Python 3.6 or higher
- Tkinter (usually included with Python)
- Additional dependencies listed in `requirements.txt`

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/afyonluoglu/Python-program-manager.git
   cd Python-program-manager
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

### Running the Application

```bash
python main.py
```

### Basic Operations

1. **Launch the Application**: Run `python main.py`
2. **Add Programs**: Use the interface to add your Python scripts and projects
3. **Organize**: Create categories and organize your programs
4. **Execute**: Launch programs directly from the manager
5. **Manage**: Edit, delete, or modify program entries

## 📁 Project Structure

```
python_program_manager/
├── main.py              # Application entry point
├── app_gui.py          # Main GUI application class
├── requirements.txt    # Python dependencies
├── README.md          # Project documentation
├── .gitignore         # Git ignore rules
└── [other modules]    # Additional application modules
```

## 🔧 Configuration

The application creates local configuration files for:
- User preferences
- Program database
- Application settings

These files are automatically created on first run and stored locally.

## 🖥️ Platform Support

- **Windows**: Full support with high DPI awareness
- **macOS**: Compatible with Tkinter
- **Linux**: Compatible with Tkinter

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Development

### Setting up Development Environment

```bash
# Clone and setup
git clone https://github.com/afyonluoglu/Python-program-manager.git
cd Python-program-manager
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add comments for complex logic
- Maintain UTF-8 encoding for all Python files

## 🐛 Troubleshooting

### Common Issues

1. **Tkinter not found**: Install `python3-tk` on Linux systems
2. **High DPI issues**: The application includes DPI awareness for Windows
3. **Import errors**: Ensure all dependencies are installed via `requirements.txt`

### Getting Help

- Check the Issues section on GitHub
- Review the documentation
- Ensure Python version compatibility

## 📄 License

This project is open source. Please check the repository for license details.

## 👨‍💻 Author

**Mustafa Afyonluoglu**
- GitHub: [@afyonluoglu](https://github.com/afyonluoglu)

## 🙏 Acknowledgments

- Built with Python and Tkinter
- Inspired by the need for better Python project organization
- Thanks to the Python community for continuous support

---

**Note**: This application creates local configuration and database files that are not included in the repository for privacy and customization purposes.
