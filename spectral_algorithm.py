import numpy as np
import pandas as pd
from openpyxl import Workbook
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from scipy.linalg import eigh, eig
from sklearn.manifold import SpectralEmbedding
from numpy import linalg
#function to read dsm from excel
def read_dsm(file_path, sheet_name):
    data = pd.read_excel(file_path, sheet_name, index_col=0) #read DSM from excel file
    adj_matrix = data.to_numpy() #convert matrix to array
    element_names = data.index.tolist() #list matrix indices (names of components)
    return adj_matrix, element_names
#random walk normalized version
def spectral_clustering(adj_matrix, k):
    n = adj_matrix.shape[0] #number of rows in matrix
    degree_matrix = np.diag(adj_matrix.sum(axis=1)) #compute degree matrix D
    L = degree_matrix - adj_matrix #compute unnormalized graph Laplacian L = D-W
    degree_inv = np.linalg.inv(degree_matrix) #compute inverse of degree matrix D^-1
    P = degree_inv @ adj_matrix #compute transition matrix P = D^-1*W
    I = np.identity(n) #identity matrix of size n by n
    Lrw = I - P #random walk Laplacian
    values, vectors =  np.linalg.eigh(Lrw) #compute eigenpairs of Lrw
    index = np.argsort(values) #record indices of elements as if they were sorted in ascending order
    values = values[index] #sort eigenvalues according to index list
    V_k = np.real(vectors[:,:k]) #select eigenvectors corresponding to the k smallest eigenvalues
    #print('First k eigenvectors:',V_k)
    return V_k #return first k eigenvectors as columns
#function to conduct kmeans and get cluster labels
def apply_kmeans(V_k, k):
    kmeans = KMeans(n_clusters=k,random_state=0).fit(V_k) #apply kmeans fit to eigenvectors
    labels = kmeans.labels_
    return labels
#function to plot cluster results in eigenspace
def plot_clusters(V_k, labels, element_names, k):
    plt.figure(figsize=(8,6))
    scatter = plt.scatter(V_k[:,0], V_k[:,1], c=labels, cmap='viridis', s=100, edgecolors='k') #create scatter plot of spectral clustering results
    for i, name in enumerate(element_names):
        plt.text(V_k[i,0], V_k[i,1], name, fontsize=9, ha='right', va='bottom') #add name of component to plot
    plt.title(f"Spectral Clustering (k={k})")
    plt.xlabel('Spectral Component 1')
    plt.ylabel('Spectral Component 2')
    plt.grid(True)
    plt.tight_layout()
    #plt.savefig(f"eigenspace_plot_k_{k}.png", dpi=300, bbox_inches='tight') #save plot as .png
    #plt.show()

#OPTIONAL: function to determine eigengap heuristic
def eigengap(adj_matrix):
    n = adj_matrix.shape[0] #number of rows in matrix
    degree_matrix = np.diag(adj_matrix.sum(axis=1)) #compute degree matrix D
    degree_inv = np.linalg.inv(degree_matrix) #compute inverse of degree matrix D^-1
    P = degree_inv @ adj_matrix #compute transition matrix P = D^-1*W
    I = np.identity(n) #identity matrix of size n by n
    Lrw = I - P #random walk Laplacian
    print('Lrw:',Lrw)
    values, vectors =  np.linalg.eigh(Lrw) #compute eigenpairs of Lrw
    index = np.argsort(values) #record indices of elements as if they were sorted
    values = values[index] #sort eigenvalues according to index list
    print('For eigengap, values:',values)
    plt.figure(figsize=(8,5)) #create plot
    plt.scatter(np.arange(1, len(values)+1), values)
    plt.title("Sorted Eigenvalues of the Laplacian")
    plt.xlabel("Index")
    plt.ylabel("Eigenvalue")
    plt.grid(True)
    #save the clustered plot to a file
    eigengap_heuristic_plot_file = 'eigengap_heuristic_plot.png'
    plt.savefig(eigengap_heuristic_plot_file, dpi=300, bbox_inches='tight') #save the figure (high resolution, remove extra whitespace)
    print(f"Eigengap plot saved as: {eigengap_heuristic_plot_file}")
    plt.show()
    index_largest_gap = np.argmax(np.diff(values))#find index of maximum difference between eigenvalues
    n_clusters = index_largest_gap + 1
    return n_clusters
#OPTIONAL: function to find spectral embedding and plot cluster results
def plot_embedding(adj_matrix, labels, element_names, k):
    embedding = SpectralEmbedding(n_components=2, affinity='precomputed', random_state=0)
    coords = embedding.fit_transform(adj_matrix)
    plt.figure(figsize=(10,8))
    scatter = plt.scatter(coords[:,0], coords[:,1], c=labels, cmap='viridis', s=100, edgecolors='k')
    for i, name in enumerate(element_names):
        plt.text(coords[i,0]+0.01, coords[i,1]+0.01, name, fontsize=10)
    plt.title(f"Spectral Clustering (k={k})")
    plt.xlabel('Spectral Component 1')
    plt.ylabel('Spectral Component 2')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"embedding_plot_k_{k}.png", dpi=300, bbox_inches='tight')
    #plt.show()

#---MAIN CODE---
if __name__ == "__main__":
    adj_matrix, names = read_dsm('ICdata.xlsm','AdjacencyMatrix') #call function to open Excel spreadsheet and read adjacency matrix
    #y = eigengap(adj_matrix)
    #print('Optimal k using eigengap:',y)
    output_file = input('Enter name of file to export results to (include .xlsx): ')
    min_modules = int(input('Enter the minimum number of modules to form: '))
    max_modules = int(input('Enter the maximum number of modules to form: '))
    print('\n')
    wb = Workbook() #create an Excel workbook
    wb.remove(wb.active) #remove default sheet
    for k in range(min_modules, max_modules+1): #for each k in a range of k values
        print(f"Running spectral clustering with k = {k}")
        V_k = spectral_clustering(adj_matrix, k) #call function to do normalized spectral clustering
        labels = apply_kmeans(V_k, k) #apply kmeans clustering to eigenvectors
        plot_clusters(V_k, labels, names, k) #call function to plot spectral results
        #plot_embedding(adj_matrix, labels, names,k)
        sheet_name = f"k_{k}" #set worksheet name
        ws = wb.create_sheet(title=sheet_name) #create worksheet in excel workbook
        ws.append(["Component", "Module"]) #add columns labeled Component and Module
        sorted_pairs = sorted(zip(names,labels), key=lambda x: x[1])
        for name, label in sorted_pairs: #for each component name and cluster label pair
            ws.append([name, int(label)]) #add to the sheet
    wb.save(output_file) #save workbook
    print("\nClustering complete!")
    print(f"Module assignment results exported to: {output_file}")


