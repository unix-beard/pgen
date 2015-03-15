Extend the pattern syntax to support the following features and types:

**Comparison (>, <, <=, >=, =, <>) operators integers (integer is going to be a new type)**

  ```{i<5}``` - Generate a digit which is less than 5
  
  ```{i>=42}```  - Generate an integer which is greater or equal to 42
  
  ```{i=2015}``` - Generate number 2015
  
  ```{i<0}``` - Generate a negative number
  
  ```{i<>-1:1}``` - Generate a number which is not -1, 0, 1
  
    
  So, the ip address pattern could be genarated like this:
  
  ```192.168.{i=0:254}.{i=1:255}``` - IP address range
  



