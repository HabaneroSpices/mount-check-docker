# Mount Check for Docker

### Installation

```bash
sudo apt install python3
git clone X && cd X
```

#### Using Venv

```bash
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 mount-check.py
```

To exit the virtual environemnt, run `deactivate`.

##### Example cronjob:

```bash
_basedir=/path/to/script_dir; source $_basedir/venv/bin/activate && python3 $_basedir/mount-check.py
```
