Extend the pattern syntax to support the following features and types:

**Comparison (>, <, <=, >=, =, <>) operators on integers (integer is going to be a new type)**

  ```{i<5}``` - Generate a digit which is less than 5
  
  ```{i>=42}```  - Generate an integer which is greater or equal to 42
  
  ```{i=2015}``` - Generate number 2015
  
  ```{i<0}``` - Generate a negative number
  
  ```{i<>-1:1}``` - Generate a number which is not -1, 0, 1
  
    
  So, the ip address pattern could be genarated like this:
  
  ```192.168.{i=0:254}.{i=1:255}``` - IP address range


**Probability operator**

  ```{alpha}{d}%50{s}%10``` - Here the probabilty of ```{d}``` to appear is 50% and ```{s}``` is 10%, respectively.
  

**PDL** (**P**attern **D**efinition **L**anguage)

```ocaml
let p = {d}{2}
print p
```

```ocaml
(* Pattern that takes another pattern as an argument *)
let p = {d}
let double p = p ~ {2}
double p    # Same as {d}{d}
double {alpha}{2}  (* Pass pattern literal as a parameter (same as {alpha}{alpha}{alpha}{alpha}) *)
```

```ocaml
let mult p quant = p ~ quant
mult {d} {5}
mult {{'John'}{'Nick'}} {@}
```

```ocaml
let node name value repeat =
    (* con is a built-in function that concatenates its arguments
     Semantically it's equivalent to p1 ~ p2 ~ ... ~ pN *)
    match name with
    | "" -> ""
    | _ -> con "<" name ">" value "</" name ">" repeat
    
node "root" (node "a" (node "b" "value of b" 3) 2) 1
```

```ocaml
let file_with_ext =
    let ext = {{"txt"}{"ini"}{"xml"}{"json"}{"md"}}{@} in
    let name = {alpha}{4:8} in
    name ~ '.' ~ ext
print file_with_ext    
```
