# Deployment

## Dependencies

* Python3

```bash
$ sudo apt install python3 python3-pip
```

* Django >= 2

```bash
$ sudo pip3 install Django
```

* zip

```bash
$ sudo apt install zip
```

## Configuration

### Django migration

```bash
$ python3 manage.py runserver
```

### Configure ducks

```bash
$ echo '<ip> <port>' >> ducks-config.txt  # For each duck
```

Or use `ducks-config.txt` generated by JudgeDuck OS.

### Configure problems

Create folder `jp_data/problems/`, and put all the problem folders into it.

The `problem_md5` of a problem would be its folder name.

## Running

```bash
$ python3 manage.py runserver <ip>:<port>
```

GL & HF !

