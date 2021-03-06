"""Module for quantum k-means algorithm with class containing sk-learn style functions resembling the k-means algorithm.

This module contains the QuantumKMeans class for clustering according to euclidian distances calculated by running quantum circuits. 

Typical usage example:

    import numpy as np
    import pandas as pd
    backend = Aer.get_backend('qasm_simulator')
    X = pd.DataFrame(np.array([[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]]))
    quantum_k_means = QuantumKMeans(backend, n_clusters=2, verbose=True)
    quantum_k_means.fit(X)
    print(kmeans.labels_)
"""
import numpy as np
import pandas as pd
from qiskit import Aer, IBMQ, execute
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from math import pi
from sklearn.preprocessing import normalize, scale
from sklearn.utils import check_random_state
from sklearn.utils. extmath import stable_cumsum

def preprocess(points,map_type='angle',norm_relevance=False):
    """Preprocesses data points according to a type criteria.

    The algorithm scales the data points if the type is 'angle' and normalizes the data points if the type is 'probability'.

    Args:

    points: The input data points.
    type: Preprocessing criteria for the data points.

    Returns:

    p_points: Preprocessed points.
    """
    if map_type == 'angle': 
        p_points = scale(points[:])
        if norm_relevance == True:
            print(p_points)
            norms = np.sqrt(p_points[:,0]**2+p_points[:,1]**2)
            max_norm = np.max(norms)
            new_column = norms/max_norm
            new_column = new_column.reshape((new_column.size,1))
            p_points = np.concatenate((p_points, new_column),axis=1)
    elif map_type == 'probability': p_points = normalize(points[:])
    return p_points

def distance(x,y,backend,shots=1024,map_type='angle',distances_in_circuit=1):
    """Calculates the distance between two data points using quantum circuits.

    The algorithm scales the data points if the type is 'angle' and normalizes the data points if the type is 'probability'.

    Args:

    x: The first data point.
    y: The second data point.
    backend: IBM quantum device to calculate the distance with.
    type: Routine for calculating distances, including data preprocessing and qubit preparation.

    Returns:

    distance: Distance between the two data points.
    """
    if distances_in_circuit == 1:
        if x.size == 2:
            if map_type == 'angle':
                complexes_x = x[0] + 1j*x[1]
                complexes_y= y[0] + 1j*y[1]
                theta_1 = np.angle(complexes_x)
                theta_2 = np.angle(complexes_y)
            
                qr = QuantumRegister(3, name="qr")
                cr = ClassicalRegister(3, name="cr")

                qc = QuantumCircuit(qr, cr, name="k_means")
                qc.h(qr[0])
                qc.h(qr[1])
                qc.h(qr[2])
                qc.u3(theta_1, pi, pi, qr[1])
                qc.u3(theta_2, pi, pi, qr[2])
                qc.cswap(qr[0], qr[1], qr[2])
                qc.h(qr[0])

                qc.measure(qr[0], cr[0])
                qc.reset(qr)
                job = execute(qc,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                if len(data)==1: return 0.0
                else: return data['001']/shots
            elif map_type == 'probability':
                qr = QuantumRegister(3, name="qr")
                cr = ClassicalRegister(3, name="cr")

                qc = QuantumCircuit(qr, cr, name="k_means")
                qc.initialize(x,1)
                qc.initialize(y,2)

                qc.h(qr[0])
                qc.cswap(qr[0], qr[1], qr[2])
                qc.h(qr[0])

                qc.measure(qr[0], cr[0])
                qc.reset(qr)
                job = execute(qc,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                if len(data)==1: return 0.0
                else: return data[list(data)[-1] == '1']
        elif x.size == 3:
            if map_type == 'angle':
                complexes_x = x[0] + 1j*x[1]
                complexes_y= y[0] + 1j*y[1]
                theta_1 = np.angle(complexes_x)
                theta_2 = np.angle(complexes_y)

                ro_1 = x[2]*np.pi
                ro_2 = y[2]*np.pi
            
                qr = QuantumRegister(3, name="qr")
                cr = ClassicalRegister(3, name="cr")

                qc = QuantumCircuit(qr, cr, name="k_means")
                qc.h(qr[0])
                qc.h(qr[1])
                qc.h(qr[2])
                qc.u3(theta_1, pi, pi, qr[1])
                qc.u3(ro_1, 0, 0, qr[1])
                qc.u3(theta_2, pi, pi, qr[2])
                qc.u3(ro_2, 0, 0, qr[1])
                qc.cswap(qr[0], qr[1], qr[2])
                qc.h(qr[0])

                qc.measure(qr[0], cr[0])
                qc.reset(qr)
                job = execute(qc,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                if len(data)==1: return 0.0
                else: return data['001']/shots
        else:
            if map_type == 'probability':
                qubits = np.ceil(np.log2(x.size))
                n_x = np.zeros(2**qubits)
                n_x[:x.size] = x
                n_y = np.zeros(2**qubits)
                n_y[:y.size] = y
                qr = QuantumRegister(2*qubits + 1, name="qr")
                cr = ClassicalRegister(2*qubits + 1, name="cr")

                qc = QuantumCircuit(qr, cr, name="k_means")
                qc.initialize(x,[i+1 for i in range(qubits)])
                qc.initialize(y,[i+1+qubits for i in range(qubits)])

                qc.h(qr[0])
                qc.cswap(qr[0], qr[1], qr[qubits+1])
                qc.h(qr[0])

                qc.measure(qr[0], cr[0])
                qc.reset(qr)
                job = execute(qc,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                if len(data)==1: return 0.0
                else: return data[list(data)[-1] == '1']
    elif distances_in_circuit > 1:
        if x[0].size == 2:
            if map_type == 'angle':
                complexes_x = x[0] + 1j*x[1]
                complexes_y= y[0] + 1j*y[1]
                theta_1 = np.angle(complexes_x)
                theta_2 = np.angle(complexes_y)
            
                qr = QuantumRegister(3, name="qr")
                cr = ClassicalRegister(3, name="cr")

                qc = QuantumCircuit(qr, cr, name="k_means")
                qc.h(qr[0])
                qc.h(qr[1])
                qc.h(qr[2])
                qc.u3(theta_1, pi, pi, qr[1])
                qc.u3(theta_2, pi, pi, qr[2])
                qc.cswap(qr[0], qr[1], qr[2])
                qc.h(qr[0])

                qc.measure(qr[0], cr[0])
                qc.reset(qr)
                job = execute(qc,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                if len(data)==1: return 0.0
                else: return data['001']/shots
            elif map_type == 'probability':
                qr = QuantumRegister(3, name="qr")
                cr = ClassicalRegister(3, name="cr")

                qc = QuantumCircuit(qr, cr, name="k_means")
                qc.initialize(x,1)
                qc.initialize(y,2)

                qc.h(qr[0])
                qc.cswap(qr[0], qr[1], qr[2])
                qc.h(qr[0])

                qc.measure(qr[0], cr[0])
                qc.reset(qr)
                job = execute(qc,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                if len(data)==1: return 0.0
                else: return data[list(data)[-1] == '1']
        elif x[0].size == 3:
            if map_type == 'angle':
                complexes_x = x[0] + 1j*x[1]
                complexes_y= y[0] + 1j*y[1]
                theta_1 = np.angle(complexes_x)
                theta_2 = np.angle(complexes_y)

                ro_1 = x[2]*np.pi
                ro_2 = y[2]*np.pi
            
                qr = QuantumRegister(3, name="qr")
                cr = ClassicalRegister(3, name="cr")

                qc = QuantumCircuit(qr, cr, name="k_means")
                qc.h(qr[0])
                qc.h(qr[1])
                qc.h(qr[2])
                qc.u3(theta_1, pi, pi, qr[1])
                qc.u3(ro_1, 0, 0, qr[1])
                qc.u3(theta_2, pi, pi, qr[2])
                qc.u3(ro_2, 0, 0, qr[1])
                qc.cswap(qr[0], qr[1], qr[2])
                qc.h(qr[0])

                qc.measure(qr[0], cr[0])
                qc.reset(qr)
                job = execute(qc,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                if len(data)==1: return 0.0
                else: return data['001']/shots
        else:
            if map_type == 'probability':
                qubits = np.ceil(np.log2(x.size))
                n_x = np.zeros(2**qubits)
                n_x[:x.size] = x
                n_y = np.zeros(2**qubits)
                n_y[:y.size] = y
                qr = QuantumRegister(2*qubits*distances_in_circuit + 1, name="qr")
                cr = ClassicalRegister(2*qubits*distances_in_circuit + 1, name="cr")

                qc = QuantumCircuit(qr, cr, name="k_means")
                for j in range(distances_in_circuit):
                    qc.initialize(x,[i+1+(qubits*j) for i in range(qubits)])
                    qc.initialize(y,[i+1+qubits+(qubits*j) for i in range(qubits)])

                    qc.h(qr[qubits*j])
                    qc.cswap(qr[qubits*j], qr[1+(qubits*j)], qr[qubits+1+(qubits*j)])
                    qc.h(qr[(qubits*j)])

                    qc.measure(qr[qubits*j], cr[qubits*j])
                qc.reset(qr)
                job = execute(qc,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                if len(data)==1: return 0.0
                else: return [data[list(data)[-1-(j*qubits+1)] == '1'] for j in range(distances_in_circuit)]


def batch_separate(X, clusters, max_experiments):
    if X.shape[0] > clusters.shape[0]:
        if X.shape[0] % max_experiments == 0: batches_X = np.asarray(np.split(X,[i*max_experiments for i in range(1,X.shape[0]//max_experiments)]))
        else: batches_X = np.asarray(np.split(X,[i*max_experiments for i in range(1,X.shape[0]//max_experiments + 1)]))
        #print("batches_X:",batches_X)
        #print(batches_X.shape)
        #print("clusters:",clusters)
        #print(clusters.shape)
        if X.shape[0] % max_experiments == 0: batches_clusters = np.empty([(X.shape[0]//max_experiments)*clusters.shape[0],clusters.shape[1]], dtype=clusters.dtype)
        else: batches_clusters = np.empty([(X.shape[0]//max_experiments + 1)*clusters.shape[0],clusters.shape[1]], dtype=clusters.dtype)
        for i in range(clusters.shape[0]):
            batches_clusters[i::clusters.shape[0]] = clusters[i]
        #print("batches_clusters:",batches_clusters)
        #print(batches_clusters.shape)
        batches_X = np.asarray(np.repeat(batches_X,clusters.shape[0],axis=0))
        #print("batches_X:",batches_X)
        #print(batches_X.shape)
        batches = [(batches_X[i], batches_clusters[i]) for i in range(batches_clusters.shape[0])]
        return batches
    else:
        raise NotImplementedError

def batch_distance(B, backend, shots=1024, map_type='angle',distances_in_circuit=1):
    if distances_in_circuit == 1:
        if B[0].shape[1] == 2:
            if map_type == 'angle':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    complexes_x = x[0] + 1j*x[1]
                    complexes_y= y[0] + 1j*y[1]
                    theta_1 = np.angle(complexes_x)
                    theta_2 = np.angle(complexes_y)
                
                    qr = QuantumRegister(3, name="qr")
                    cr = ClassicalRegister(3, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.h(qr[0])
                    qc.h(qr[1])
                    qc.h(qr[2])
                    qc.u3(theta_1, pi, pi, qr[1])
                    qc.u3(theta_2, pi, pi, qr[2])
                    qc.cswap(qr[0], qr[1], qr[2])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()

                return [batch_data['001']/shots if len(batch_data)!=1 else 0.0 for batch_data in data]
            elif map_type == 'probability':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    qr = QuantumRegister(3, name="qr")
                    cr = ClassicalRegister(3, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.initialize(x,1)
                    qc.initialize(y,2)

                    qc.h(qr[0])
                    qc.cswap(qr[0], qr[1], qr[2])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                contained = ['0'*2+'1' in batch_data for batch_data in data]
                return [data[i]['0'*2+'1']/shots if contained[i]==True else 0.0 for i in range(len(contained))]
        elif B[0].shape[1] == 3:
            if map_type == 'angle':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    complexes_x = x[0] + 1j*x[1]
                    complexes_y= y[0] + 1j*y[1]
                    theta_1 = np.angle(complexes_x)
                    theta_2 = np.angle(complexes_y)
                
                    ro_1 = x[2]*np.pi/2
                    ro_2 = y[2]*np.pi/2

                    qr = QuantumRegister(3, name="qr")
                    cr = ClassicalRegister(3, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.h(qr[0])
                    qc.h(qr[1])
                    qc.h(qr[2])
                    qc.u3(theta_1, pi, pi, qr[1])
                    qc.u3(ro_1, 0, 0, qr[1])
                    qc.u3(theta_2, pi, pi, qr[2])
                    qc.u3(ro_2, 0, 0, qr[2])
                    qc.cswap(qr[0], qr[1], qr[2])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()

                return [batch_data['001']/shots if len(batch_data)!=1 else 0.0 for batch_data in data]
        elif np.log2(B[0].shape[1]).is_integer():
            if map_type == 'angle':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    complexes_x = x[0] + 1j*x[1]
                    complexes_y= y[0] + 1j*y[1]
                    theta_1 = np.angle(complexes_x)
                    theta_2 = np.angle(complexes_y)
                
                    qr = QuantumRegister(3, name="qr")
                    cr = ClassicalRegister(3, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.h(qr[0])
                    qc.h(qr[1])
                    qc.h(qr[2])
                    qc.u3(theta_1, pi, pi, qr[1])
                    qc.u3(theta_2, pi, pi, qr[2])
                    qc.cswap(qr[0], qr[1], qr[2])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()

                return [batch_data['001']/shots if len(batch_data)!=1 else 0.0 for batch_data in data]
            elif map_type == 'probability':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    qr = QuantumRegister(int(np.log2(B[0].shape[1]))*2+1, name="qr")
                    cr = ClassicalRegister(int(np.log2(B[0].shape[1]))*2+1, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.initialize(x,[i+1 for i in range(int(np.log2(B[0].shape[1])))])
                    qc.initialize(y,[i+1+int(np.log2(B[0].shape[1])) for i in range(int(np.log2(B[0].shape[1])))])

                    qc.h(qr[0])     
                    qc.cswap(qr[0], qr[1], qr[int(np.log2(B[0].shape[1])+1)])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                contained = ['0'*int(np.log2(B[0].shape[1]))*2+'1' in batch_data for batch_data in data]
                return [data[i]['0'*int(np.log2(B[0].shape[1]))*2+'1']/shots if contained[i]==True else 0.0 for i in range(len(contained))]
        else:
            if map_type == 'angle':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    complexes_x = x[0] + 1j*x[1]
                    complexes_y= y[0] + 1j*y[1]
                    theta_1 = np.angle(complexes_x)
                    theta_2 = np.angle(complexes_y)
                
                    qr = QuantumRegister(3, name="qr")
                    cr = ClassicalRegister(3, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.h(qr[0])
                    qc.h(qr[1])
                    qc.h(qr[2])
                    qc.u3(theta_1, pi, pi, qr[1])
                    qc.u3(theta_2, pi, pi, qr[2])
                    qc.cswap(qr[0], qr[1], qr[2])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()

                return [batch_data['001']/shots if len(batch_data)!=1 else 0.0 for batch_data in data]
            elif map_type == 'probability':
                qcs = []
                for point in B[0]:
                    if np.log2(B[0].shape[1]).is_integer(): qubits = int(np.log2(B[0].shape[1]))
                    else: qubits = int(np.log2(B[0].shape[1])) + 1
                    x = np.zeros(2**qubits)
                    x[:point.shape[0]] = point
                    y = np.zeros(2**qubits)
                    y[:B[1].shape[0]] = B[1]
                    qr = QuantumRegister(qubits*2+1, name="qr")
                    cr = ClassicalRegister(qubits*2+1, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.initialize(x,[i+1 for i in range(qubits)])
                    qc.initialize(y,[i+1+qubits for i in range(qubits)])

                    qc.h(qr[0])     
                    qc.cswap(qr[0], qr[1], qr[qubits+1])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                contained = ['0'*qubits*2+'1' in batch_data for batch_data in data]
                return [data[i]['0'*qubits*2+'1']/shots if contained[i]==True else 0.0 for i in range(len(contained))]
    elif distances_in_circuit > 1:
        if B[0].shape[1] == 2:
            if map_type == 'angle':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    complexes_x = x[0] + 1j*x[1]
                    complexes_y= y[0] + 1j*y[1]
                    theta_1 = np.angle(complexes_x)
                    theta_2 = np.angle(complexes_y)
                
                    qr = QuantumRegister(3, name="qr")
                    cr = ClassicalRegister(3, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.h(qr[0])
                    qc.h(qr[1])
                    qc.h(qr[2])
                    qc.u3(theta_1, pi, pi, qr[1])
                    qc.u3(theta_2, pi, pi, qr[2])
                    qc.cswap(qr[0], qr[1], qr[2])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()

                return [batch_data['001']/shots if len(batch_data)!=1 else 0.0 for batch_data in data]
            elif map_type == 'probability':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    qr = QuantumRegister(3, name="qr")
                    cr = ClassicalRegister(3, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.initialize(x,1)
                    qc.initialize(y,2)

                    qc.h(qr[0])
                    qc.cswap(qr[0], qr[1], qr[2])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                contained = ['0'*2+'1' in batch_data for batch_data in data]
                return [data[i]['0'*2+'1']/shots if contained[i]==True else 0.0 for i in range(len(contained))]
        elif B[0].shape[1] == 3:
            if map_type == 'angle':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    complexes_x = x[0] + 1j*x[1]
                    complexes_y= y[0] + 1j*y[1]
                    theta_1 = np.angle(complexes_x)
                    theta_2 = np.angle(complexes_y)
                
                    ro_1 = x[2]*np.pi/2
                    ro_2 = y[2]*np.pi/2

                    qr = QuantumRegister(3, name="qr")
                    cr = ClassicalRegister(3, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.h(qr[0])
                    qc.h(qr[1])
                    qc.h(qr[2])
                    qc.u3(theta_1, pi, pi, qr[1])
                    qc.u3(ro_1, 0, 0, qr[1])
                    qc.u3(theta_2, pi, pi, qr[2])
                    qc.u3(ro_2, 0, 0, qr[2])
                    qc.cswap(qr[0], qr[1], qr[2])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()

                return [batch_data['001']/shots if len(batch_data)!=1 else 0.0 for batch_data in data]
        elif np.log2(B[0].shape[1]).is_integer():
            if map_type == 'angle':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    complexes_x = x[0] + 1j*x[1]
                    complexes_y= y[0] + 1j*y[1]
                    theta_1 = np.angle(complexes_x)
                    theta_2 = np.angle(complexes_y)
                
                    qr = QuantumRegister(3, name="qr")
                    cr = ClassicalRegister(3, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.h(qr[0])
                    qc.h(qr[1])
                    qc.h(qr[2])
                    qc.u3(theta_1, pi, pi, qr[1])
                    qc.u3(theta_2, pi, pi, qr[2])
                    qc.cswap(qr[0], qr[1], qr[2])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()

                return [batch_data['001']/shots if len(batch_data)!=1 else 0.0 for batch_data in data]
            elif map_type == 'probability':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    qr = QuantumRegister(int(np.log2(B[0].shape[1]))*2+1, name="qr")
                    cr = ClassicalRegister(int(np.log2(B[0].shape[1]))*2+1, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.initialize(x,[i+1 for i in range(int(np.log2(B[0].shape[1])))])
                    qc.initialize(y,[i+1+int(np.log2(B[0].shape[1])) for i in range(int(np.log2(B[0].shape[1])))])

                    qc.h(qr[0])     
                    qc.cswap(qr[0], qr[1], qr[int(np.log2(B[0].shape[1])+1)])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                contained = ['0'*int(np.log2(B[0].shape[1]))*2+'1' in batch_data for batch_data in data]
                return [data[i]['0'*int(np.log2(B[0].shape[1]))*2+'1']/shots if contained[i]==True else 0.0 for i in range(len(contained))]
        else:
            if map_type == 'angle':
                qcs = []
                for point in B[0]:
                    x = point
                    y = B[1]
                    complexes_x = x[0] + 1j*x[1]
                    complexes_y= y[0] + 1j*y[1]
                    theta_1 = np.angle(complexes_x)
                    theta_2 = np.angle(complexes_y)
                
                    qr = QuantumRegister(3, name="qr")
                    cr = ClassicalRegister(3, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.h(qr[0])
                    qc.h(qr[1])
                    qc.h(qr[2])
                    qc.u3(theta_1, pi, pi, qr[1])
                    qc.u3(theta_2, pi, pi, qr[2])
                    qc.cswap(qr[0], qr[1], qr[2])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()

                return [batch_data['001']/shots if len(batch_data)!=1 else 0.0 for batch_data in data]
            elif map_type == 'probability':
                qcs = []
                for point in B[0]:
                    if np.log2(B[0].shape[1]).is_integer(): qubits = int(np.log2(B[0].shape[1]))
                    else: qubits = int(np.log2(B[0].shape[1])) + 1
                    x = np.zeros(2**qubits)
                    x[:point.shape[0]] = point
                    y = np.zeros(2**qubits)
                    y[:B[1].shape[0]] = B[1]
                    qr = QuantumRegister(qubits*2*distances_in_circuit+1, name="qr")
                    cr = ClassicalRegister(qubits*2*distances_in_circuit+1, name="cr")

                    qc = QuantumCircuit(qr, cr, name="k_means")
                    qc.initialize(x,[i+1 for i in range(qubits)])
                    qc.initialize(y,[i+1+qubits for i in range(qubits)])

                    qc.h(qr[0])     
                    qc.cswap(qr[0], qr[1], qr[qubits+1])
                    qc.h(qr[0])

                    qc.measure(qr[0], cr[0])
                    qc.reset(qr)
                    qcs.append(qc)
                job = execute(qcs,backend=backend, shots=shots)
                result = job.result()
                data = result.get_counts()
                contained = ['0'*qubits*2+'1' in batch_data for batch_data in data]
                return [data[i]['0'*qubits*2+'1']/shots if contained[i]==True else 0.0 for i in range(len(contained))]


def batch_collect(batch_d, desired_shape):
    #print('Batch d is', batch_d)
    #print('Batch d shape is', batch_d.shape)
    #print('Desired shape is', desired_shape)
    final_batch_d = np.empty(batch_d.shape, dtype=batch_d.dtype)
    #print('Final Batch D is', final_batch_d)
    batch_rounds = batch_d.shape[0]//desired_shape[0]
    counter = 0
    for i in range(desired_shape[0]):
        for j in range(batch_rounds):
            final_batch_d[counter] = batch_d[i+j*desired_shape[0]]
            counter += 1
    #print('Final Batch D is', final_batch_d)
    #for i in range(batch_d.shape[0]//desired_shape[0]):
    #    final_batch_d[i] = batch_d[desired_shape[0]*i]
    #print('Final Batch D is', final_batch_d)
    #for i in range(batch_d.shape[0]//desired_shape[0],batch_d.shape[0]):
    #    final_batch_d[i] = batch_d[desired_shape[0]*i-batch_d.shape[0]+1]
    distances = []
    counter = 0
    distances_row = []
    for i in range(batch_d.shape[0]):
        distances_row += final_batch_d[i]
        if counter == (batch_d.shape[0]//desired_shape[0])-1:
            distances.append(distances_row)
            distances_row = []
            counter=0
        else:
            counter+=1
    #print('Distances are',np.array(distances))
    return np.array(distances)

def batch_distances(X, cluster_centers, backend, shots, map_type, verbose):
    if isinstance(cluster_centers, pd.DataFrame): batches = batch_separate(X.to_numpy(), cluster_centers.to_numpy(),backend.configuration().max_experiments)
    else: batches = batch_separate(X.to_numpy(), cluster_centers,backend.configuration().max_experiments*(backend.configuration().n_qubits//np.ceil(np.log2(X.shape[1]))))
    print('Batches are', batches)
    distance_list = np.asarray([batch_distance(B, backend, shots, map_type) for B in batches])
    print('Distance list is', distance_list)
    distances = batch_collect(distance_list, (cluster_centers.shape[0],X.shape[0]))    
    print('Distances are', distances)  
    return distances 

def qkmeans_plusplus(X, n_clusters, backend, shots, map_type, verbose, initial_center, x_squared_norms=None, n_local_trials=None, random_state=None):
    if verbose: print('Started Qkmeans++')
    random_state = check_random_state(random_state)
    n_samples, n_features = X.shape
    
    centers = np.empty((n_clusters, n_features), dtype= X.values.dtype)

    if n_local_trials is None:
        n_local_trials = 2 + int(np.log(n_clusters))

    center_id = random_state.randint(n_samples)
    indices = np.full(n_clusters, -1, dtype=int)
    indices[0] = center_id
    centers[0] = X.values[center_id]

    if verbose: print('Centers are:', centers)

    closest_distances = batch_distances(X, centers[0, np.newaxis], backend, shots, map_type, verbose)
    current_pot = closest_distances.sum()

    #if verbose: print('Closest distances are:', closest_distances)

    for c in range(1, n_clusters):
        if verbose: print('Cluster center', c)
        rand_vals = random_state.random_sample(n_local_trials) * current_pot
        candidate_ids = np.searchsorted(stable_cumsum(closest_distances), rand_vals)

        np.clip(candidate_ids, None, closest_distances.size - 1, out=candidate_ids)

        distance_to_candidates = batch_distances(X, X.values[candidate_ids], backend, shots, map_type, verbose)

        np.minimum(closest_distances, distance_to_candidates,
                   out=distance_to_candidates)
        candidates_pot = distance_to_candidates.sum(axis=1)

        best_candidate = np.argmin(candidates_pot)
        current_pot = candidates_pot[best_candidate]
        closest_distances = distance_to_candidates[best_candidate]
        best_candidate = candidate_ids[best_candidate]

        centers[c] = X.values[best_candidate]
        indices[c] = best_candidate

        if verbose: print('Centers are:', centers)
        #if verbose: print('Closest distances are:', closest_distances)

        if c == 1 and initial_center == 'far':
            closest_distances = batch_distances(X, centers[1, np.newaxis], backend, shots, map_type, verbose)
            current_pot = closest_distances.sum()
            rand_vals = random_state.random_sample(n_local_trials) * current_pot
            candidate_ids = np.searchsorted(stable_cumsum(closest_distances), rand_vals)

            np.clip(candidate_ids, None, closest_distances.size - 1, out=candidate_ids)

            distance_to_candidates = batch_distances(X, X.values[candidate_ids], backend, shots, map_type, verbose)

            np.minimum(closest_distances, distance_to_candidates,
                    out=distance_to_candidates)
            candidates_pot = distance_to_candidates.sum(axis=1)

            best_candidate = np.argmin(candidates_pot)
            current_pot = candidates_pot[best_candidate]
            closest_distances = distance_to_candidates[best_candidate]
            best_candidate = candidate_ids[best_candidate]

            centers[0] = X.values[best_candidate]
            indices[0] = best_candidate

            if verbose: print('Centers are:', centers)
    
    return centers, indices

class QuantumKMeans():
    """Quantum k-means clustering algorithm. This k-means alternative implements Quantum Machine Learning to calculate distances between data points and centroids using quantum circuits.
    
    Args:
        n_clusters: The number of clusters to use and the amount of centroids generated.
        init: {'qk-means++, 'random'}, callable or array-like of shape (n_clusters, n_features) Method for initialization:
        'qk-means++' : selects initial cluster centers for qk-mean clustering in a smart way to speed up convergence.
        'random': choose n_clusters observations (rows) at random from data for the initial centroids.
        If an array is passed, it should be of shape (n_clusters, n_features) and gives the initial centers.
        If a callable is passed, it should take arguments X, n_clusters and a random state and return an initialization.
        tol: Relative tolerance with regards to Frobenius norm of the difference in the cluster centers of two consecutive iterations to declare convergence.
        verbose: Defines if verbosity is active for deeper insight into the class processes.
        max_iter: Maximum number of iterations of the quantum k-means algorithm for a single run.
        backend: IBM quantum device to run the quantum k-means algorithm on.
        type: {'angle', 'probability'} Specify the type of data encoding.
        'angle': Uses U3 gates with its theta angle being the phase angle of the complex data point.
        'probability': Relies on data normalization to preprocess the data to acquire a norm of 1.

    Attributes:
        cluster_centers_: Coordinates of cluster centers.
        labels_: Centroid labels for each data point.
        n_iter_: Number of iterations run before convergence.
    """
    def __init__(self, backend=IBMQ.load_account().get_backend('ibmq_qasm_simulator'), shots=1024, n_clusters=2, init='qk-means++', tol=0.0001, max_iter=300, verbose=False, map_type='angle', norm_relevance=False, initial_center='random'):
        """Initializes an instance of the quantum k-means algorithm."""
        self.cluster_centers_ = np.empty(0)
        self.labels_ = np.empty(0)
        self.inertia_ = 0
        self.inertias_ = np.empty(0)
        self.n_iter_ = 0
        self.n_clusters = n_clusters
        self.init = init
        self.tol = tol
        self.verbose = verbose
        self.max_iter = max_iter
        self.backend = backend
        self.shots = shots
        self.map_type = map_type
        self.norm_relevance = norm_relevance
        self.initial_center = initial_center
    
    def fit(self, X, batch=True):
        """Computes quantum k-means clustering.
        
        Args:
            X: Training instances to cluster.
            batch: Option for using batches to calculate distances.

        Returns:
            self: Fitted estimator.
        """
        finished = False
        X = pd.DataFrame(preprocess(X, self.map_type, self.norm_relevance))
        if self.verbose: print('Data is:',X)
        if self.init == 'qk-means++': 
            self.cluster_centers_, _ = qkmeans_plusplus(X, self.n_clusters, self.backend, self.shots, self.map_type, self.verbose, self.initial_center)
            self.cluster_centers_ = pd.DataFrame(self.cluster_centers_)
        elif self.init == 'random': self.cluster_centers_ = X.sample(n=self.n_clusters).reset_index(drop=True)
        iteration = 0
        previous_inertia = 0
        print('Self init is', self.init)
        while not finished and iteration<self.max_iter:
            if self.verbose: print("Iteration",iteration)
            if batch: distances = batch_distances(X, self.cluster_centers_, self.backend, self.shots, self.map_type, self.verbose)   
            else: distances = np.asarray([[distance(point, centroid, self.backend, self.shots) for _, point in X.iterrows()] for _, centroid in self.cluster_centers_.iterrows()])
            #print('distances are',distances)
            #print('distances shape is', distances.shape)
            self.labels_ = np.asarray([np.argmin(distances[:,i]) for i in range(distances.shape[1])])
            #print('labels are',self.labels_)
            #print('labels shape is',self.labels_.shape)
            if self.map_type == 'angle': new_centroids = X.groupby(self.labels_).mean()
            elif self.map_type == 'probability': new_centroids = pd.DataFrame(preprocess(X.groupby(self.labels_).mean(),self.map_type))
            if self.verbose: print("Old centroids are",self.cluster_centers_)
            if self.verbose: print("New centroids are",new_centroids)
            self.inertia_ = np.square(np.linalg.norm(X.values - self.cluster_centers_.values[self.labels_])).sum(axis=0).sum()
            if self.verbose: print("Inertia is",self.inertia_)
            if abs(previous_inertia - self.inertia_) < self.tol:
                finished = True
            self.inertias_ = np.append(self.inertias_, self.inertia_)
            previous_inertia = self.inertias_[-1]
            self.cluster_centers_ = new_centroids
            if self.verbose: print("Centers are", self.labels_)
            self.n_iter_ += 1
            iteration += 1
        return self

    def predict(self, X, sample_weight = None, batch = True):
        """Predict the closest cluster each sample in X belongs to.

        Args:
            X: New data points to predict.
            sample_weight: The weights for each observation in X. If None, all observations are assigned equal weight.

        Returns:
            labels: Centroid labels for each data point.
        """
        X = pd.DataFrame(preprocess(X, self.map_type, self.norm_relevance))
        if sample_weight is None:
            if batch: distances = batch_distances(X, self.cluster_centers_, self.backend, self.shots, self.map_type, self.verbose) 
            else: distances = np.asarray([[distance(point, centroid, self.backend, self.shots) for _,point in X.iterrows()] for _,centroid in self.cluster_centers_.iterrows()])
        else: 
            weight_X = X * sample_weight
            if batch: batch_distances(weight_X, self.cluster_centers_, self.backend, self.shots, self.map_type, self.verbose)
            else: distances = np.asarray([[distance(point, centroid, self.backend, self.shots) for _,point in weight_X.iterrows()] for _,centroid in self.cluster_centers_.iterrows()])
        labels = np.asarray([np.argmin(distances[:,i]) for i in range(distances.shape[1])])
        return labels

    def get_params(self, deep=True):
        """Get parameters for this estimator.
        
        Args:
            deep: If True, will return the parameters for this estimator and contained subobjects that are estimators.

        Returns:
            params: Parameter names mapped to their values.
        """
        return {"n_clusters": self.n_clusters, "init": self.init, "tol": self.tol, "verbose": self.verbose, "max_iter": self.max_iter, "backend": self.backend, "shots": self.shots, "map_type": self.map_type, "norm_relevance": self.norm_relevance, "initial_center": self.initial_center }

    def set_params(self, **params):
        """Set the parameters of this estimator.
        
        Args:
            **params: Estimator parameters.

        Returns:
            self: Estimator instance.
        """
        for parameter, value in params.items():
            setattr(self, parameter, value)
        return self     