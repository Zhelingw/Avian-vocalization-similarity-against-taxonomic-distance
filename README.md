We were motivated to see the correlation between closeness of avian classification, and the similarity in their songs and calls. 

This is to compare the sounds that birds make and how similar they are, to how close the birds are genetically related. By cross-analyzing these two sets of data, we want to answer the hypothesis if or if not the way they sound can be determined purely from the taxonomic distance of birds.
 
Thus, it raises our research question: *how close do bird species relate to each other based on the similarity of their vocalization?*

Since analyzing vocalizations of all avians is infeasible, we focused on some members of the three families paridae, fringillidae, and phylloscopidae under the order Passeriformes, as these are some families of the most numbers of species in Passeriformes and so are more representative; we also used recordings from some species of the orders Strigiformes and Piciformes, in order to increase the distances between species. 

Based on our processed data, about 50 unique sepcies, 500 recordings, and a total of 2259 comparisons were performed. Using the complete processed data, the Pearson correlation coefficient is calculated to be -0.2441, while the coefficient of determination $\text{R}^2$ is 0.0596. The p-value is less than 0.001. 

This means there is a negative correlation between Taxonomic Distance and Vocalization Similarity, and this relationship is statistically highly significant ($p < 0.001$). Also, 5.96\% of the variation in the vocalization similarity is determined by changes in the taxonomic distance, which is able to directly answer our research question. 

To run the project, simply download all files, and run `main.py`. `bird_data` is the folder of all our used data; if it's too large, then extract `partial_bird_data.zip` into the same directory as `main.py`. The libraries required are listed in `requirements.txt`.

When running the project, figures 1 and 2 will be displayed in the web browser, which shows scatter plot of data between single species with all others, and the full chart. 
Figure 3 is the interactive chart that also displays in the browser after clicking on the link of the server form the console. You can zoom in and out of the tree, and select certain species. Doing so will play a recording of that species, and also color all other species, where red represents a more similar vocalization, and blue represents less similar. Figure 4 shows the interactive coloring. 
After stopping the taxonomy tree in the console by ctrl+C, a standard deviation graph is shown, like that of figure 5. 

<img width="718" height="1170" alt="Screenshot 2026-04-23 at 15 21 08" src="https://github.com/user-attachments/assets/d4bc2c25-8634-4f2a-85e5-37d8fac0b046" />

<img width="744" height="994" alt="Screenshot 2026-04-23 at 15 21 15" src="https://github.com/user-attachments/assets/bad79986-6e33-437e-900f-8686b6c4ff8d" />


The whole report can be seen in report_Avian_Taxonomic_Distance_and_Vocalization_Similarities.pdf, including used datasets, computational overviews of the Taxonomy Tree, calculations of vocalization similarity, and interactive visualizations, and further discussions. A list of references is also found towards the end of the file. 
