# Yang CLI

This tool allows to automatically generate a CLI based on a set of Yang models.

It also permits to generate RESTCONF calls based on the filled data using the CLI.

The pyang plugin "navigator" in the plugin folder generates as an output a "data.txt" file, which is used by the yang_cli.py python script.

## How to use

Example for pyang navigator plugin.

```bash
pyang -f navigator ietf-l3vpn-svc.yang -p . -o out.tree
```

Example for yang_cli.py:

```bash
python yang_cli.py data.txt
```

The _data.txt_ provided as an example is based on the L3SM YANG model from IETF (RFC 8299).

## Commands

- __save__: it allows to save the data in the JSON format used by the tool to store and explore the YANG files.
- __saverc__: similar as the previous one, but the JSON complies with RFC 7951. _If the data configured does not comply with the standard (e.g. a key is not configured) this command may not succeed._
- __load__: it allows to load the data in the JSON format used by the tool to store and explore the YANG files.
- __loadrc__: similar as the previous one, but the JSON shall comply with RFC 7951. _If the data to be loaded does not comply with the standard (e.g. a given key is not in the file) this command may not succeed._
- __pwd__: it displays the path on which the user is.
- __show-config__: displays the config done by the user so far.
- __delete__: deletes the element on the path where the user is, moving the current path to one step lower in the configuration hierarchy.
- __rc__: command to generate RESTCONF calls, following the format shown in IETF RFCs. It asks for the operation to be implemented (POST, PUT, PATCH, DELETE, GET).
- __back__: moves the current path to one step lower in the configuration hierarchy.
- __exit__: goes out of the yang_cli. Any configuration not saved will disappear.

## Dependencies

Pyang

Prompt toolkit:
sudo pip  install -U prompt-toolkit==2.0.7
