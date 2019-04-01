# -*- coding: utf-8 -*-

from util.plot import plot_list

path_to_img_lst = "./test/resources/newseye_as_test_data/image_paths.lst"
path_to_hyp_lst = "./test/resources/newseye_as_test_data/hy_xml_paths.lst"
path_to_gt_lst = "./test/resources/newseye_as_test_data/gt_xml_paths.lst"

# path_to_img_lst = "./test/resources/newseye_as_test_data_onb/image_paths.lst"
# path_to_hyp_lst = "./test/resources/newseye_as_test_data_onb/hy_xml_paths.lst"
# path_to_gt_lst = "./test/resources/newseye_as_test_data_onb/gt_xml_paths.lst"

# path_to_img_lst = "./test/resources/Le_Matin_Set/image_paths.lst"
# path_to_hyp_lst = "./test/resources/Le_Matin_Set/hy_xml_paths.lst"
# path_to_gt_lst = "./test/resources/Le_Matin_Set/gt_xml_paths.lst"


plot_list(img_lst=path_to_img_lst, hyp_lst=path_to_hyp_lst, gt_lst=path_to_gt_lst,
          plot_article=True, force_equal_names=True)
