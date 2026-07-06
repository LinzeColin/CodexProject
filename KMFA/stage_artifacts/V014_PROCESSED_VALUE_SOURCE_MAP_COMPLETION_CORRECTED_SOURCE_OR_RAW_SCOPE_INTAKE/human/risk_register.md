# Risk Register

- Risk: treating scope registration as value matching.
  Mitigation: raw file listing, parsing, hashing and comparison remain blocked.
- Risk: leaking raw path or filenames publicly.
  Mitigation: public artifacts contain only booleans and scope codes; private path stays ignored.
