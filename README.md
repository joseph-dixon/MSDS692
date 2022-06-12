# Setlist Comparison with the setlist.fm API, MongoDB, and Edit Distance Algorithms
Ask any "Deadhead" and they'll proudly tell you that the Grateful Dead never repeated a setlist. This may very well be true, but after touring for three decades and playing thousands of shows, the question must be asked: how close did they get?

This question spurred an idea for an end-to-end project that could accept a simple plain-text CLI input, digest an artists's setlist corpus, and run a comparison algorithm that would identify the most similar setlists in the corpus. This is possible through a robust setlist.fm API, a local database (MongoDB in this case, for schema flexibility), and some algorithm to compare arrays.

The algorithm is inspired by the concept of an <b>edit distance</b>, which traditionally represents the difference between two strings numerically. To give an example, the edit distance between "minding" and "bonding" would be two, as two letters ("m" -> "b" and "i" -> "o") must be changed to make the words identical.

This algorithm considers the following factors: whether the same songs exist between two setlists and the order in which the songs appear. To do this, it builds a sparse matrix where each row is a setlist and the columns are each individual song in the corpus as well as each unique two-song combination that appears in the corpus. Beginning and endings of setlists are signified with a placeholder string.

The algorithm then iteratively compares each row against every other row in the sparse matrix and extracts the most similar setlist. It does this by summing the two arrays and dividing the number of twos (i.e. identical values in columns) by the number of non-zero values in the resultant array. To reduce runtime, each row is only compared against rows it hasn't "seen" before. In other words, if we compare Row A with Rows B and C, when the algorithm moves to Row B, it only needs to look at Row C.

Once similarity scores have been computed for each row in the sparse matrix, the algorithm pulls out the highest value.
