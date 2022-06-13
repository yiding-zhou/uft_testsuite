#!/bin/sh

pip3 install -r requirements.txt

cd ../rpc
python3 -m grpc_tools.protoc -I./ --python_out=. --grpc_python_out=. flow.proto
python3 -m grpc_tools.protoc -I./ --python_out=. --grpc_python_out=. qos.proto

cd -
mv ../rpc/*.py core/

python3 start.py
