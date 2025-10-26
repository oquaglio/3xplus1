#

## Get biggest number scanned

```sh
watch -n 0.5 'printf "Scanning up to: %'\''d\n" $(tail -1 collatz_checkpoint.txt 2>/dev/null || echo 0)'
```
