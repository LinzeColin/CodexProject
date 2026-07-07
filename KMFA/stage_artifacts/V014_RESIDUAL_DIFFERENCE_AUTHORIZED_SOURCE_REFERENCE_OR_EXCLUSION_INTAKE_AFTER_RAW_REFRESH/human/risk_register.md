# Risk Register

- Risk: intake queue is mistaken for authoritative source binding.
- Control: all binding, comparison and downstream gate flags remain false.
- Risk: private slot or resolution details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private details stay ignored.
- Risk: raw inbox is modified.
- Control: this phase does not access raw inbox and preserves raw immutability.
