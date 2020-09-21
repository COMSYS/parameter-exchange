# Web Interface

The web interface is mainly designed for testing and to provide an overview of the provided functionality.
Not all functionality is accessible via the web interface.

Key Server: `https://localhost:5000/`
Storage Server: `https://localhost:5001/`

## Authentication

The web interface uses two different types of authentication mechanisms.
Some pages (Main, Token, Status, Task, Kill) use the combination of username + password and the remaining pages use username + one-time-token (previously generated).

### Sample Users

To generate sample users, the script `configureTestSetup.sh` can be used.
This script generates the following users:

	Client with
		username: testuser
		password: password

	Provider with
		username: testuser
		password: password

	Provider with
		username: testprovider
		password: password

### Own Users

Users can be created via the database tools `owner_db_cli.py` and `client_db_cli.py`. See option `-h` for details.

### Generate Tokens

Tokens can either be generated via the `Gen. Token` page of the web interface or via the following scripts:

Provider:

	python3 owner_db_cli.py USERNAME PASSWORD -t

Client:

	python3 client_db_cli.py USERNAME PASSWORD -t

Tokens for Storage and Key server are **not** compatible.
Moreover, each token can only be used **once**.
Afterward, a new token has to be generated.

### Access Mechanism by Page

The following list shows which page is accessible via which authentication mechanism. The username always has to be used, therefore, the list only states whether a password or a token is needed.

#### Key Server

	Client
		Token: Password
		Hash Key: Token
		Key Retrieval: Token
		Status: Password
			Task: Password
			Kill: Password

	Provider
		Token: Password
		Hash Key: Token
		Key Retrieval: Token
		Status: Password
			Task: Password
			Kill: Password

#### Storage Server

	Client
		Gen. Token: Password
		Bloom: Token
		PSI: Token
		Status: Password
			Task: Password
			Kill: Password

	Provider
		Gen. Token: Password
		Batch Store: Token, but this page does not provide any functionality, just linked for overview
		Status: Password
			Task: Password
			Kill: Password


## Client Applications for PSI and Key Retrieval

If a PSI or OT (key retrieval) has been started via the web interface, separate client tools have to be used to interact with the server instances.
For PSIs, the tool `PSIReceiver.py` can be used, and, for OTs, the tool `OTReceiver.py`. See option `-h` for details.

### Examples

Retrieve 10 keys via OT from port 12345 on localhost:

	python3 OTReceiver.py -p 12345 10

Perform a PSI with set size 100 with an instance on port 12345 on localhost:

	python3 PSIReceiver.py -p 12345 100