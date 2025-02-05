# CS Map Overlay TTS

A game overlay for **Counter-Strike (CS)** that detects enemy positions on the minimap and uses **text-to-speech (TTS)** to announce their locations in real-time. The overlay displays the detected positions on the screen, making it easier for players to react quickly.

## Features
- **Enemy Detection**: Detects enemy positions based on the minimap in the game.
- **Text-to-Speech (TTS)**: Announces enemy locations using TTS (text-to-speech).
- **Real-time Updates**: Updates the overlay with new enemy locations as they are detected.
- **Customizable Settings**: Adjust settings like key bindings, TTS voice options, and text display.
- **Hotkeys**: Easily toggle the display of the overlay and the enemy detection system using customizable hotkeys.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/cs-map-overlay-tts.git
   ```

2. **Install required dependencies**:
   Ensure you have Python 3.x installed. Then, install the dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   After installing the dependencies, run the script:
   ```bash
   python your_script_name.py
   ```

## Requirements
- Python 3.x
- The following libraries:
  - **mss**: For screen capturing.
  - **opencv-python**: For image processing and enemy detection.
  - **numpy**: For array handling.
  - **pyttsx3**: For text-to-speech (TTS).
  - **keyboard**: For hotkey detection.

You can install the dependencies from the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

## Configuration
Once the application is running, the overlay will display detected enemy locations on the screen and announce them via TTS. The settings allow you to control:

- **Text Display**: Show or hide the enemy position information on the screen.
- **TTS Settings**: Control the volume, speech rate, and TTS voice.
- **Hotkeys**: Configure hotkeys for toggling the display and controlling TTS.
  
### Key Hotkeys
- **Toggle Text Display**: Set your preferred key (e.g., `F11`).
- **Toggle Enemy Detection**: Set your preferred key (e.g., `F10`).
- **Toggle TTS**: Set your preferred key (e.g., `F8`).

## Usage
- When running the software, it will detect enemy positions on the minimap in **Counter-Strike** and display them on the screen.
- The TTS system will announce enemy positions in real-time.
- You can use the hotkeys to toggle the display and the enemy detection system on and off.

## Example Workflow
1. **Launch the game** (Counter-Strike).
2. **Run the application** (the overlay will automatically detect the minimap and enemies).
3. **Use the hotkeys** to control whether you want to hear the announcements or see the text overlay.

## Future Improvements
- Support for other games and custom minimap formats.
- Enhancements to the TTS system for more realistic voice options.
- Additional customization options for the overlay display.

## Troubleshooting

### 1. **Issue with TTS not working**
   - Ensure that `pyttsx3` is installed and properly configured.
   - Make sure that your microphone/speaker settings allow audio output.

### 2. **Enemy detection not working**
   - Ensure that the game window is not minimized.
   - Check that the minimap area is not obstructed or changed by game settings.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements
- **OpenCV**: Used for image processing and minimap recognition.
- **pyttsx3**: Used for text-to-speech conversion.
- **mss**: Used for screen capturing in real-time.

## Contact Information
- Join the QQ group for discussions and support: **891346430**.
- You can also check out the Bilibili channel of the creator by searching for **孤帆233**.
