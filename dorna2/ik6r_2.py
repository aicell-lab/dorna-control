import numpy as np
from dorna2.cf import CF
from dorna2.ik6r_matrix import sigma_matrix
from dorna2.poly import poly

#File containing for a 6-r manipulator with non-zero DH parameters: a2,a3,d1,-d4,d5,d6,d7
#The algorithm is originaly based on: Raghavan(1993): "Inverse Kinematics of the General 6R Manipulator and Related Linkages"
#The polynomial computation also takes inspiration from Gomez et al. "A faster algorithm for calculating the inverse kinematics of a general 6R manipulator for robot real time control"
#The calculation of determinant algorithm is based on: Bird(2011) "A simple division-free algorithm for computing determinants"


def copy_matrix(s):
	result = [[s[j][i] for i in range(len(s))] for j in range(len(s))]
	return result

def matrix_evaluated(A,x3):
	result = [[0 for i in range(12)] for j in range(12)]
	for i in range(12):
		for j in range(12):
			result[i][j] = A[i][j].evaluate(x3)
	return result


def pstr(matrix):
	for i in range(12):
		print(str(matrix[i][0]) + "," + str(matrix[i][1]) + "," + str(matrix[i][2]) + "," + str(matrix[i][3]) + "," + str(matrix[i][4]) + "," + str(matrix[i][5]) + "," + str(matrix[i][6]) + "," + str(matrix[i][7]) + "," + str(matrix[i][8]) + "," + str(matrix[i][9]) + "," + str(matrix[i][10]) + "," + str(matrix[i][11]))


def ik(a2,a3,d1,d4,d5,d6,d7,mat):
	#name the input
	f11=mat[0,0]
	f12=mat[0,1]
	f13=mat[0,2]
	f14=mat[0,3]*10.0

	f21=mat[1,0]
	f22=mat[1,1]
	f23=mat[1,2]
	f24=mat[1,3]*10.0

	f31=mat[2,0]
	f32=mat[2,1]
	f33=mat[2,2]
	f34=mat[2,3]*10.0

	a2 *= 10.0
	a3 *= 10.0
	d1 *= 10.0
	d4 *= 10.0
	d5 *= 10.0
	d6 *= 10.0
	d7 *= 10.0

	#find the matrix and make a copy of it for later
	try:
		g = sigma_matrix(a2,a3,d1,d4,d5,d6,d7,f13,f23,f33,f14,f24,f34)
	except:
		print("divison by zero")
		return []
	original_g = copy_matrix(g)

	#find the 16th order determinant polynomial
	res = []
	poly_mat = []
	
	for x3 in range(-8,9):
		v = x3/4
		#det_v = -det_m(matrix_evaluated(g,v))/(1+v**2)**4
		det_v = np.linalg.det(matrix_evaluated(g,v))/(1+v**2)**4
		res.append([det_v] )
		
		poly_row = []
		for i in range(17):
			poly_row.append(np.pow(v,i))
		poly_mat.append(poly_row)

	res= np.array(res)
	poly_mat = np.array(poly_mat)
	inv_poly_mat = np.linalg.inv(poly_mat)
	poly_multipliers = np.matmul(inv_poly_mat,res)

	det = poly((poly_multipliers.T)[0])
	det.normalize()


	#find all roots, and choose the real ones
	roots = np.roots(det.coefficients[::-1])
	#print("roots : ", x3_list)
	x3_list = roots.real[abs(roots.imag)<1e-5]
	res = []
	

	for x3 in x3_list:
		#print("root:",x3,"has value: ",det.evaluate(x3))
		theta3 = 2*np.atan(x3)
		matrix = matrix_evaluated(original_g,x3)
		matrix_t = [row[:11] for row in matrix[1:12]]
		#print("det:",np.linalg.det(np.array(matrix_t)))

		#print("mat_t:",np.linalg.det(matrix_t))

		inv_matrix_t = np.linalg.inv(np.array(matrix_t))
		matrix_right = np.array([[row[11] for row in matrix[1:12]]]).T

		ff = np.matmul(inv_matrix_t, -matrix_right)
		#print("ff:",ff)
		x5 = ff[10]
		x4 = ff[8]

		theta4 = 2*np.atan(x4)
		theta5 = 2*np.atan(x5)
		c3 = np.cos(theta3)
		s3 = np.sin(theta3)
		c4 = np.cos(theta4)
		s4 = np.sin(theta4)
		c5 = np.cos(theta5)
		s5 = np.sin(theta5)

		den = (f14*f23 - f13*f24)
		for i in range(2):
			
			if abs(den)>1e-5:
				if i==1:
					break
				c1 = ((-d4)*f13 + d6*f13*c4 + (d7*f13 - f14)*s4*s5)/den
				s1 = ((-d4)*f23 + d6*f23*c4 + (d7*f23 - f24)*s4*s5)/den
			else:
				c1 = (1-2*i)* ((-d4)*f13 + d6*f13*c4 + (d7*f13 - f14)*s4*s5)
				s1 = (1-2*i)*((-d4)*f23 + d6*f23*c4 + (d7*f23 - f24)*s4*s5)	

			theta1 = np.atan2(s1,c1)
			c1 = np.cos(theta1)
			s1 = np.sin(theta1)
			
			den = (f33**2 + f13**2*c1**2 + f23**2*s1**2 + f13*f23*np.sin(2*theta1))		
			c2 =  -(((-f33)*(c5*s3 + c3*c4*s5) - (f13*c1 + f23*s1)*(c3*c5 -c4*s3*s5))/den)
			s2 = ((-s3)*(f13*c1*c5 + f23*c5*s1 + f33*c4*s5) + c3*(f33*c5 - c4*(f13*c1 + f23*s1)*s5))/den
			theta2 = np.atan2(s2,c2)

			den = (c1**2*(f21**2 + f22**2) - 2*c1*(f11*f21 + f12*f22)*s1 + (f11**2 + f12**2)*s1**2)
			c6 = (s1*(c4*f12 + c5*f11*s4) - c1*(c4*f22 + c5*f21*s4)) / den
			s6 =  ((-c1)*c4*f21 + c4*f11*s1 + c1*c5*f22*s4 - c5*f12*s1*s4) /den
			theta6 = np.atan2(s6,c6)

			res.append([theta1,theta2,theta3,theta4,theta5,theta6])
	return res
	

if __name__ == '__main__':

	mat = [[-(1+np.sqrt(3))/(2*np.sqrt(2)),0,0.25*(np.sqrt(2)-np.sqrt(6)),0.25*(8+np.sqrt(2)*(3-np.sqrt(3)))]
			,[0,-1,0,0],
			[0.25*(np.sqrt(2)-np.sqrt(6)),0,0.25*(np.sqrt(2)+np.sqrt(6)),0.25*(4+np.sqrt(2)*(3+np.sqrt(3)))],
			[0,0,0,1]]
