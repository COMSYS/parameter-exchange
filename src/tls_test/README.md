# TLS Perfomance Evaluation

These scripts allow to evaluate the local TLS performance.

## Configuration

The tested protocol version, cipher suite and curve can be defined at the top
 of `tls_client.py`.
 
 It may be necessary to adapt `echo_server.sh` accordingly.
 The `-msg` option in `echo_server.sh` allows to print handshake messages to
  verify the used cipher and curve.
  
## Execution

First start `echo_server.sh` in one terminal and then start `tls_client.py
` in another terminal.
If you want to generate a csv, use the `-o basename` Option of `tls_client.py`.
Files are written to `eval/tls/basename_cipher_curve.csv `.
