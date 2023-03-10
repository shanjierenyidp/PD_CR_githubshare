from torch_cluster import radius
import torch
from torch_scatter import scatter
 

class FeatureDescriptors(object):
    """Computes a feature descriptor based on the outer product of positions difference and normals difference between
    neighbouring vertices. Requires normals being available for each vertex.

    Args:
        r (float): Neighbourhood radius from which to compute the differences.
    """

    def __init__(self, r = 2):
        self.r = r

    def __call__(self, data):
        descriptor_list = []
        for ri in [self.r,self.r*2,self.r*3,self.r*4,self.r*5,self.r*6]:
            index = radius(data.pos, data.pos, ri)

            difference = data.pos[index[1]] - data.pos[index[0]]
            distance = torch.linalg.norm(difference, dim=1)

            weight = (self.r - distance)

            difference = difference / self.r
            normal = data.norm[index[1]]

            descriptor = torch.cat([self.feature(difference, difference, index[0], weight).unsqueeze(1),
                                    self.feature(normal, normal, index[0], weight).unsqueeze(1),
                                    self.feature(difference, normal, index[0], weight).unsqueeze(1)], dim=1)
            descriptor_list.append(descriptor)
            
        #adding features with different r 
        data.featr = descriptor_list[0]
        data.featr2 = descriptor_list[1]
        data.featr3 = descriptor_list[2]
        data.featr4 = descriptor_list[3]
        data.featr5 = descriptor_list[4]
        data.featr6 = descriptor_list[5]

        return data

    @staticmethod
    def feature(a, b, i, weight):
        matrix = torch.bmm(a.view(-1, 3, 1), b.view(-1, 1, 3))  # batch matrix multiplication
        matrix = weight.view(-1, 1, 1) * matrix

        average = scatter(matrix, i, dim=0, reduce='sum')

        # if torch.all(torch.eq(a, b)):  # symmetric
        #     return average[:, [0, 0, 0, 1, 1, 2], [0, 1, 2, 1, 2, 2]]  # flattened upper triangular

        # else:
        #     return average.view(-1, 9)  # flatten

        return average

    def __repr__(self):
        return '{}(r={})'.format(self.__class__.__name__, self.r)



