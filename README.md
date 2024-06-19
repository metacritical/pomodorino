# Pomodorino 🍅

Pomodorino is a lightweight, terminal-based Pomodoro timer designed to boost your productivity using the Pomodoro Technique. This simple yet effective tool helps you manage your work sessions and breaks directly from your command line.

## Features

- **Customizable Work and Break Intervals**: Set your own durations for work sessions and breaks.
- **Pause and Resume**: Pause your session with 'p' and resume with 'p'.
- **Quit Anytime**: Exit the timer using 'q' or the Escape key.
- **Notifications**: Receive desktop notifications to alert you when it's time to work or take a break (supports macOS and Linux).

## Installation

Clone this repository to your local machine:

```sh
git clone https://github.com/yourusername/pomodorino.git
```

### Make the script executable:

```sh
chmod +x pomo

```

### Usage=
Run the timer with:

```sh
./pomo

```

### During the timer, you can:

    •	Pause: Press p to pause the timer.
	•	Resume: Press p again to resume the timer.
	•	Quit: Press q or the Escape key to exit the timer.
    
    
### Customization

You can customize the durations of the work sessions, short breaks, and long breaks by editing the variables at the top of the pomo script:

# Pomodoro durations


```sh
POMODORO_DURATION=25  # Pomodoro work duration in minutes
SHORT_BREAK=5         # Short break duration in minutes
LONG_BREAK=15         # Long break duration in minutes
POMODOROS_BEFORE_LONG_BREAK=4

```

### Notifications

For macOS, the script uses osascript to display notifications. Ensure your system allows notifications from the terminal.

For Linux, the script uses notify-send. Make sure notify-send is installed on your system:


```sh
sudo apt-get install libnotify-bin

```

### Contributing

Feel free to fork this repository and submit pull requests. Any improvements or suggestions are welcome!

#### License

This project is licensed under the MIT License. See the [LICENSE](https://opensource.org/license/mit) link for details.

### Acknowledgments

	•	Inspired by the Pomodoro Technique developed by Francesco Cirillo.
	•	Emoji icons from Twemoji.

Made with ❤️ by Pankaj Doharey
