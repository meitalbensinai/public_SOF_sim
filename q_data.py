__author__ = 'Meital'
# data that were used to examine the keyword extraction approach


dict_of_info = {}
dict_of_info[363681] = {'title': "Generating random integers in a range with Java", 'content': """I am trying to generate a random integer with Java, but random in a specific range. For example, my range is 5-10, meaning that 5 is the smallest possible value the random number can take, and 10 is the biggest. Any other number in between these numbers is possible to be a value, too.

In Java, there is a method random() in the Math class, which returns a double value between 0.0 and 1.0. In the class Random there is a method nextInt(int n), which returns a random integer value in the range of 0 (inclusive) and n (exclusive). I couldn't find a method, which returns a random integer value between two numbers.

I have tried the following things, but I still have problems: (minimum and maximum are the smallest and biggest numbers).

Solution 1:

Solution 2:

How do I solve this problem?

I have tried also browsing through the archive and found:

Expand a random range from 1-5 to 1-7
Generate random numbers uniformly over an entire range
But I couldn't solve the problem.""", 'tags': 'java range random', 'code': """Random ran = new Random();
int x = ran.nextInt(6) + 5;"""}

dict_of_info[38987] = {'title': 'Converting a string to byte-array without using an encoding (byte-by-byte)', 'content': """How do I convert a string to a byte[] in .NET (C#)?

Update: Also please explain why encoding should be taken into consideration. Can't I simply get what bytes the string has been stored in? Why is there a dependency on character encodings?""", 'tags': "c# string", 'code': """static byte[] GetBytes(string str)
{
    byte[] bytes = new byte[str.Length * sizeof(char)];
    System.Buffer.BlockCopy(str.ToCharArray(), 0, bytes, 0, bytes.Length);
    return bytes;
}

static string GetString(byte[] bytes)
{
    char[] chars = new char[bytes.Length / sizeof(char)];
    System.Buffer.BlockCopy(bytes, 0, chars, 0, bytes.Length);
    return new string(chars);
}"""}

dict_of_info[53513] = {"title": "Best way to check if a list is empty", "content": """For example, if passed the following:
How do I check to see if a is empty?""", 'tags': 'python list', "code": """if not a:
  print "List is empty"""""}

dict_of_info[5585779] = {'title': "Converting String to int in Java?", 'content': """How can a String be converted to an int in Java?

My String contains only numbers and I want to return the number it represents.

For example, given the string "1234" the result should be the number 1234.""", 'tags': "java string type-conversion", "code": """int foo = Integer.parseInt("1234");"""}

dict_of_info[46898] = {"title": "Iterate over each Entry in a Map", "content": """If I have an object implementing the Map interface in Java and I wish to iterate over every pair contained within it, what is the most efficient way of going through the map?

Will the ordering of elements depend on the specific map implementation that I have for the interface?""", "tags": "java map iteration", "code": """for (Map.Entry<String, String> entry : map.entrySet())
{
    System.out.println(entry.getKey() + "/" + entry.getValue());
} """}

dict_of_info[29361031] = {"title": "Regex for mobile number with maximum number of 10", "content": """Here's what I've tried so far. Is there something wrong with my Regex?

What i did was values must be numbers only and with a maximum number of 10. I have no idea what my code doesn't catch when I input more than 10 numbers.""", "tags": "ios", "code": "/^(\+\d{1,3}[- ]?)?\d{10}$/"}

dict_of_info[29095967] = {"title": "Splitting List into sublists along elements", "content": """I have this list :

And I'd like something like this:

In other words I want to split my list in sublists using the null value as separator, in order to obtain a list of lists . I'm looking for a Java 8 solution. I've tried with  but I'm not sure it is what I'm looking for. Thanks!""", "tags":"java list java-8 collectors", "code": """List<String> strings = Arrays.asList("a", "b", null, "c", null, "d", "e");
    List<List<String>> groups = strings.stream()
            .collect(() -> {
                List<List<String>> list = new ArrayList<>();
                list.add(new ArrayList<>());
                return list;
            },
            (list, s) -> {
                if (s == null) {
                    list.add(new ArrayList<>());
                } else {
                    list.get(list.size() - 1).add(s);
                }
            },
            (list1, list2) -> {
                // Simple merging of partial sublists would
                // introduce a false level-break at the beginning.
                list.get(list.size() - 1).addAll(list2.remove(0));
                list1.addAll(list2);
            }); """}

dict_of_info[28942758] = {"title": "How do I get the dimensions (nestedness) of a nested vector (NOT the size)?", "content": """Consider the following declarations:

vector<vector<int> > v2d;
vector<vector<vector<string>> > v3d;
How can I find out the "dimensionality" of the vectors in subsequent code? For example, 2 for v2d and 3 for v3d?""", "tags": "c++ vector", "code": """template<typename T>
int getDims(const T& vec)
{
   return 0;
}
template<typename T>
int getDims(const vector<T>& vec)
{
   return getDims(T{})+1;
}"""}