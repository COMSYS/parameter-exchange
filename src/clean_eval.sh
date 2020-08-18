#!/usr/bin/env bash

rm ../data/*.log
rm -r ../data/eval
while true; do
    read -p "Do you want to delete eval results, too? [Y/n]" yn
    case $yn in
        [Yy]* ) rm -r ../eval/*; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
