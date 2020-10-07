# Self Adapting Smart Home Assistant (SASHA)

SASHA is a Python module providing a local privacy by design smart home assistant based on Rhasspy. It features self adaptation, command detection without wake word and free positioning of wake word through constant listening.  

## Requirements 

Install Docker via convenience script 

```
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```
If you would like to use Docker as a non-root user, you should now consider adding your user to the “docker” group with something like:
```
sudo usermod -aG docker your-user
```
Remember to log out and back in for this to take effect!

Next install docker-compose via [pip](https://pip.pypa.io/en/stable/).
```
sudo pip install docker-compose
```

## Installation

Clone this repository to install SASHA.
```git
git clone https://shedz@bitbucket.org/shedz/sasha.git
```
### Alsa Config
In order to enable the usage of microphone and sound output add the following alsa config file under ~/.asoundrc
```
pcm.!default {
    type asym
    capture.pcm "input"
    playback.pcm "output"
}
pcm.input {
    type plug
    slave {
        pcm "hw:2,0"
    }
}
pcm.output {
    type plug
    slave {
        pcm "hw:1,0"
        rate 16000
    }
}


ctl.!default {
        type hw
        card  1
}
``` 
You may have to adjust the soundcard numbers. Just check the used cards with aplay / arecord -l.

### Connecting the components
1. Change the IP address in __ init__.py to the address of your localhost.
2. Setup Home Assistant Generate Long Lived Access Token in the user menu
3. Select Home Assistant as execution component for Rhasspy and enter the <address of you localhost>:8123/

### Setting Up Snips NLU
1. Follow Rhasspy [Wiki](rhasspy.readthedocs.io) to setup SnipsNLU via advanced configuration
2. Create Snips profile folder
```
mkdir ~/.config/rhasspy/profiles/en/snips
```

## Usage

From within the repository folder call:
```
docker-compose up
```
Now the interface of Rhasspy is available via localhost port 12101 and Home Assistant interface on port 8123.

While running, SASHA has the ability to self adapt the command patterns with the transcriptions of sentences that frequently occured before the actual commands.
To set up how often a sentence has to occurr change the THRESHOLD variable in ```__init__.py``` to the value you want. By Default it is 3

Commands added this way are added to the slots interface of Rhasspy and can be modified or deleted there. Currently only alternative command patterns
for simple commands are supported. As otherwise the slots cannot be set correctly. In order to fix this a more complex Home Assistant configuration is necessary.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)